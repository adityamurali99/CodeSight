import * as vscode from 'vscode';
import axios from 'axios';

// 1. Updated collection name
const diagnostics = vscode.languages.createDiagnosticCollection('coderift');

export function activate(context: vscode.ExtensionContext) {
    console.log('Coderift is now active!');

    context.subscriptions.push(
        vscode.languages.registerCodeActionsProvider('python', new CoderiftFixer(), {
            providedCodeActionKinds: CoderiftFixer.providedCodeActionKinds
        })
    );

    // 2. Updated command ID to 'coderift.review'
    let reviewCmd = vscode.commands.registerCommand('coderift.review', async () => {
        const editor = vscode.window.activeTextEditor;
        if (!editor) return;

        // 3. Updated config call to 'coderift'
        const config = vscode.workspace.getConfiguration('coderift');
        const userApiKey = config.get<string>('openaiApiKey')?.trim() || "";

        if (userApiKey === "") {
            vscode.window.showErrorMessage("Coderift: OpenAI API Key not found.", "Open Settings").then(selection => {
                if (selection === "Open Settings") {
                    vscode.commands.executeCommand('workbench.action.openSettings', 'coderift');
                }
            });
            return; 
        }

        const document = editor.document;
        vscode.window.withProgress({
            location: vscode.ProgressLocation.Notification,
            title: "Coderift",
            cancellable: false
        }, async (progress) => {
            progress.report({ message: "Analyzing code..." });

            try {
                const RAILWAY_URL = 'https://codesight-production-0b9f.up.railway.app'; 
                const response = await axios.post(`${RAILWAY_URL}/analyze-local`, {
                    code: document.getText(),
                    fileName: document.fileName,
                    apiKey: userApiKey
                });

                const { findings, summary } = response.data;
                diagnostics.clear();
                const newDiagnostics: vscode.Diagnostic[] = [];

                findings.forEach((issue: any) => {
                    const line = Math.max(0, (issue.line_number || 1) - 1);
                    const range = new vscode.Range(line, 0, line, 100);
                    const diagnostic = new vscode.Diagnostic(range, `[AI Review] ${issue.issue}`, vscode.DiagnosticSeverity.Error);
                    (diagnostic as any).fixedCode = issue.suggestion || ""; 
                    diagnostic.code = "apply_ai_fix";
                    newDiagnostics.push(diagnostic);
                });

                diagnostics.set(document.uri, newDiagnostics);
                vscode.window.showInformationMessage(`Review Complete: ${summary}`);
            } catch (error: any) {
                vscode.window.showErrorMessage(`Coderift Failed: ${error.message}`);
            }
        });
    });

    context.subscriptions.push(reviewCmd);
}

export function deactivate() {}

// Fixer class renamed for consistency
export class CoderiftFixer implements vscode.CodeActionProvider {
    public static readonly providedCodeActionKinds = [vscode.CodeActionKind.QuickFix];
    public provideCodeActions(document: vscode.TextDocument, range: vscode.Range, context: vscode.CodeActionContext): vscode.CodeAction[] {
        return context.diagnostics
            .filter(d => d.code === "apply_ai_fix")
            .map(d => this.createFix(document, d));
    }
    private createFix(document: vscode.TextDocument, diagnostic: vscode.Diagnostic): vscode.CodeAction {
        const fix = new vscode.CodeAction(`Apply AI Fix: ${diagnostic.message}`, vscode.CodeActionKind.QuickFix);
        fix.edit = new vscode.WorkspaceEdit();
        const replacement = (diagnostic as any).fixedCode;
        if (replacement) fix.edit.replace(document.uri, diagnostic.range, replacement);
        fix.diagnostics = [diagnostic];
        fix.isPreferred = true;
        return fix;
    }
}