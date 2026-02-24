import * as vscode from 'vscode';
import axios from 'axios';

// Managed collection for the "red squiggles" in the editor
const diagnostics = vscode.languages.createDiagnosticCollection('codesight');

export function activate(context: vscode.ExtensionContext) {
    console.log('CodeSight is now active!');

    // 1. Register the Quick Fix Provider at startup
    context.subscriptions.push(
        vscode.languages.registerCodeActionsProvider('python', new CodeSightFixer(), {
            providedCodeActionKinds: CodeSightFixer.providedCodeActionKinds
        })
    );

    // 2. Register the Review Command
    let reviewCmd = vscode.commands.registerCommand('codesight.review', async () => {
        const editor = vscode.window.activeTextEditor;
        
        if (!editor) {
            vscode.window.showErrorMessage("Please open a file to review.");
            return;
        }

        // --- BYOK (Bring Your Own Key) SECURITY CHECK ---
        const config = vscode.workspace.getConfiguration('codesight');
        const userApiKey = config.get<string>('openaiApiKey')?.trim() || "";

        if (userApiKey === "") {
            vscode.window.showErrorMessage(
                "CodeSight: OpenAI API Key not found. Please configure it in settings to protect your usage limits.",
                "Open Settings"
            ).then(selection => {
                if (selection === "Open Settings") {
                    vscode.commands.executeCommand('workbench.action.openSettings', 'codesight');
                }
            });
            return; // EXIT: Do not proceed to the API call
        }
        // ------------------------------------------------

        const document = editor.document;
        const code = document.getText();
        const fileName = document.fileName;

        vscode.window.withProgress({
            location: vscode.ProgressLocation.Notification,
            title: "CodeSight",
            cancellable: false
        }, async (progress) => {
            progress.report({ message: "Analyzing code with your API Key..." });

            try {
                // Point this to your local server (127.0.0.1:8000) for testing 
                // or your Railway URL for production
                const RAILWAY_URL = 'https://codesight-production-0b9f.up.railway.app'; 
                
                const response = await axios.post(`${RAILWAY_URL}/analyze-local`, {
                    code: code,
                    fileName: fileName,
                    apiKey: userApiKey // Passing the validated key
                });

                const { findings, summary } = response.data;

                // Clear old diagnostics and update with new ones
                diagnostics.clear();
                const newDiagnostics: vscode.Diagnostic[] = [];

                findings.forEach((issue: any) => {
                    const line = Math.max(0, (issue.line_number || issue.line || 1) - 1);
                    const range = new vscode.Range(line, 0, line, 100);

                    const diagnostic = new vscode.Diagnostic(
                        range,
                        `[AI Review] ${issue.issue}`,
                        vscode.DiagnosticSeverity.Error
                    );

                    // Attach the fix data to the diagnostic object
                    (diagnostic as any).fixedCode = issue.suggestion || issue.fix || ""; 
                    diagnostic.code = "apply_ai_fix";

                    newDiagnostics.push(diagnostic);
                });

                diagnostics.set(document.uri, newDiagnostics);
                vscode.window.showInformationMessage(`Review Complete: ${summary}`);

            } catch (error: any) {
                console.error("Analysis Error:", error);
                const errorMsg = error.response?.data?.detail || error.message;
                vscode.window.showErrorMessage(`CodeSight Failed: ${errorMsg}`);
            }
        });
    });

    context.subscriptions.push(reviewCmd);
}

export function deactivate() {
    diagnostics.clear();
}

/**
 * Logic for the "Lightbulb" menu to apply AI suggestions
 */
export class CodeSightFixer implements vscode.CodeActionProvider {
    public static readonly providedCodeActionKinds = [
        vscode.CodeActionKind.QuickFix
    ];

    public provideCodeActions(
        document: vscode.TextDocument, 
        range: vscode.Range | vscode.Selection, 
        context: vscode.CodeActionContext
    ): vscode.CodeAction[] {
        return context.diagnostics
            .filter(diagnostic => diagnostic.code === "apply_ai_fix")
            .map(diagnostic => this.createFix(document, diagnostic));
    }

    private createFix(document: vscode.TextDocument, diagnostic: vscode.Diagnostic): vscode.CodeAction {
        const fix = new vscode.CodeAction(`Apply AI Fix: ${diagnostic.message}`, vscode.CodeActionKind.QuickFix);
        fix.edit = new vscode.WorkspaceEdit();
        
        const replacement = (diagnostic as any).fixedCode;
        if (replacement) {
            fix.edit.replace(document.uri, diagnostic.range, replacement);
        }
        
        fix.diagnostics = [diagnostic];
        fix.isPreferred = true;
        return fix;
    }
}