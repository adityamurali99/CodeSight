import * as vscode from 'vscode';
import axios from 'axios';

// This collection manages the "red squiggles" in the editor
const diagnostics = vscode.languages.createDiagnosticCollection('codesight');

export function activate(context: vscode.ExtensionContext) {
    console.log('Congratulations, "CodeSight" is now active!');

    let reviewCmd = vscode.commands.registerCommand('codesight.review', async () => {
        const editor = vscode.window.activeTextEditor;
        
        if (!editor) {
            vscode.window.showErrorMessage("Please open a file to review.");
            return;
        }

        const document = editor.document;
        const code = document.getText();
        const fileName = document.fileName;

        // 1. Visual feedback that the AI is working
        vscode.window.withProgress({
            location: vscode.ProgressLocation.Notification,
            title: "CodeSight",
            cancellable: false
        }, async (progress) => {
            progress.report({ message: "Analyzing code with Railway Brain..." });

            try {
                // 2. The Request
                const RAILWAY_URL = 'https://codesight-production-0b9f.up.railway.app'; 
                const response = await axios.post(`${RAILWAY_URL}/analyze-local`, {
                    code: code,
                    fileName: fileName
                });

                const { findings, summary } = response.data;

                // 3. Clear old issues and set new ones
                diagnostics.clear();
                const newDiagnostics: vscode.Diagnostic[] = [];

                findings.forEach((issue: any) => {
                    // 1. Map the line correctly (handling Python's 1-indexing)
                    const line = Math.max(0, (issue.line_number || issue.line || 1) - 1);
                    const range = new vscode.Range(line, 0, line, 100);

                    const diagnostic = new vscode.Diagnostic(
                        range,
                        `[AI Review] ${issue.issue}`,
                        vscode.DiagnosticSeverity.Error
                    );

                    // 2. STASH THE DATA FOR THE QUICK FIX
                    // Use 'suggestion' to match your latest Python Pydantic model
                    (diagnostic as any).fixedCode = issue.suggestion || issue.fix || ""; 
                    
                    // This key tells our Provider "this squiggle has a fix available"
                    diagnostic.code = "apply_ai_fix";

                    newDiagnostics.push(diagnostic);
                });
                diagnostics.set(document.uri, newDiagnostics);
                vscode.window.showInformationMessage(`Review Complete: ${summary}`);

            } catch (error: any) {
                console.error("Analysis Error:", error);
                vscode.window.showErrorMessage(`Railway Connection Failed: ${error.message}`);
            }

            context.subscriptions.push(
                vscode.languages.registerCodeActionsProvider('python', new CodeSightFixer(), {
                    providedCodeActionKinds: CodeSightFixer.providedCodeActionKinds
                })
            );
        });
    });

    context.subscriptions.push(reviewCmd);
}

export function deactivate() {
    diagnostics.clear();
}

export class CodeSightFixer implements vscode.CodeActionProvider {
    public static readonly providedCodeActionKinds = [
        vscode.CodeActionKind.QuickFix
    ];

    provideCodeActions(document: vscode.TextDocument, range: vscode.Range | vscode.Selection, context: vscode.CodeActionContext): vscode.CodeAction[] {
        // For every diagnostic (squiggle) at the current cursor position
        return context.diagnostics
            .filter(diagnostic => diagnostic.code?.hasOwnProperty('value') && (diagnostic.code as any).value === "apply_ai_fix")
            .map(diagnostic => this.createFix(document, diagnostic));
    }

    private createFix(document: vscode.TextDocument, diagnostic: vscode.Diagnostic): vscode.CodeAction {
        const fix = new vscode.CodeAction(`Apply AI Fix: ${diagnostic.message}`, vscode.CodeActionKind.QuickFix);
        fix.edit = new vscode.WorkspaceEdit();
        
        // Retrieve that fixed code we stashed earlier
        const replacement = (diagnostic as any).fixedCode;
        
        if (replacement) {
            // This replaces the specific line with the AI's suggested code
            fix.edit.replace(document.uri, diagnostic.range, replacement);
        }
        
        fix.diagnostics = [diagnostic];
        fix.isPreferred = true;
        return fix;
    }
}

