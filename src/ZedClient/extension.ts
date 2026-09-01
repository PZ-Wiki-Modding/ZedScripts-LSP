import * as vscode from 'vscode';
import { LanguageClient, TransportKind } from "vscode-languageclient/node";

export async function activate(context: vscode.ExtensionContext) {
    const serverOptions = {
        command: "/home/simon/Documents/Repositories/LSP/ZedScripts-LSP/.venv/bin/python",
        args: ["-m", "ZedScripts.main"],
        transport: TransportKind.stdio,
    };
    
    const clientOptions = {
        documentSelector: [{ scheme: "file", language: "plaintext" }],
    };
    
    const client = new LanguageClient(
        "zedserver",
        "Zed Server",
        serverOptions,
        clientOptions,
    );
    
    context.subscriptions.push(client);
    await client.start();
}

// This method is called when your extension is deactivated
export function deactivate() {}
