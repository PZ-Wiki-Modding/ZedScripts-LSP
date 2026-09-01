"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.activate = activate;
exports.deactivate = deactivate;
const node_1 = require("vscode-languageclient/node");
async function activate(context) {
    const serverOptions = {
        command: "/home/simon/Documents/Repositories/LSP/ZedScripts-LSP/.venv/bin/python",
        args: ["-m", "ZedScripts.main"],
        transport: node_1.TransportKind.stdio,
    };
    const clientOptions = {
        documentSelector: [{ scheme: "file", language: "plaintext" }],
    };
    const client = new node_1.LanguageClient("zedserver", "Zed Server", serverOptions, clientOptions);
    context.subscriptions.push(client);
    await client.start();
}
// This method is called when your extension is deactivated
function deactivate() { }
//# sourceMappingURL=extension.js.map