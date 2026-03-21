# VS Code Session ID – Zugriffsmöglichkeiten

> **VS Code Version:** 1.112.0 | **Stand:** März 2026

---

## Übersicht

VS Code bietet aktuell **keine einzige stabile öffentliche API**, die direkt eine `sessionId` als String zurückgibt. Stattdessen gibt es je nach Anwendungsfall mehrere Wege, eine eindeutige Session-ID zu ermitteln oder zu nutzen.

| Anwendungsfall | Methode |
|---|---|
| Session-ID aus laufender Session lesen | Methode 1 – OTel JSONL |
| Debugging & Analyse offline | Methode 2 – Agent Debug Panel Export |
| Background Agent (Copilot CLI) | Methode 3 – `~/.copilot/session-state/` |
| Eigene VS Code Extension | Methode 4 – `toolInvocationToken` |

---

## Methode 1: OpenTelemetry (OTel) – Empfohlen

Das ist der sauberste und zuverlässigste Weg. VS Code Copilot Chat kann Telemetriedaten via OpenTelemetry exportieren. Die `session.id` steckt als Resource-Attribut in jedem exportierten Span, `gen_ai.conversation.id` korreliert alle Signale einer Session.

### Einrichtung (`settings.json`)

```json
{
  "github.copilot.chat.otel.enabled": true,
  "github.copilot.chat.otel.exporterType": "file",
  "github.copilot.chat.otel.outfile": "C:/tmp/copilot-otel.jsonl"
}
```

> Environment-Variablen haben immer Vorrang vor VS Code Settings. Alternativ kann als `exporterType` auch `"otlp-grpc"` mit einem lokalen Dashboard (z. B. Aspire) verwendet werden.

### Format der JSONL-Ausgabe

Jede Zeile ist ein Span-Objekt im OTLP-Format:

```json
{
  "resourceSpans": [{
    "resource": {
      "attributes": [
        { "key": "session.id",       "value": { "stringValue": "abc-123-uuid" } },
        { "key": "service.name",     "value": { "stringValue": "copilot-chat" } },
        { "key": "service.version",  "value": { "stringValue": "0.35.x" } }
      ]
    },
    "scopeSpans": [{
      "spans": [{
        "name": "invoke_agent",
        "attributes": [
          { "key": "gen_ai.conversation.id", "value": { "stringValue": "abc-123-uuid" } }
        ]
      }]
    }]
  }]
}
```

**Relevante Felder:**

- `session.id` – eindeutige ID der VS Code Session (Resource-Ebene)
- `gen_ai.conversation.id` – ID der Konversation (für Korrelation über mehrere Spans)
- `copilot_chat.session.start` – Event, das beim Session-Start emittiert wird

---

## Methode 2: Agent Debug Log Panel (VS Code 1.112)

Seit VS Code 1.112 kann man Debug-Sessions als **OpenTelemetry JSON (OTLP-Format)** exportieren und importieren. Das Panel zeigt chat-Events in Echtzeit und enthält die Session-ID.

### Aktivierung

```json
{
  "github.copilot.chat.agentDebugLog.enabled": true,
  "github.copilot.chat.agentDebugLog.fileLogging.enabled": true
}
```

### Panel öffnen

Über die Command Palette:
```
Developer: Open Agent Debug Panel
```
Oder: Zahnrad-Icon im Chat-View → **View Agent Logs**

### Export / Import

1. Agent Debug Logs Panel öffnen
2. Session auswählen
3. **Export-Icon** (Download) in der Toolbar klicken → speichert als `.json` (OTLP-Format)
4. Die exportierte Datei enthält die Session-ID in den Resource-Attributen (identisch zu Methode 1)

> **Hinweis:** Das Agent Debug Panel ist aktuell nur für lokale Chat-Sessions verfügbar. Import von Dateien > 50 MB zeigt eine Warnung.

---

## Methode 3: Copilot CLI Session-State Files (Background Agents)

Für **Copilot CLI / Background Agent Sessions** werden Session-State-Dateien lokal gespeichert. Der Dateiname entspricht direkt der Session-ID.

### Speicherort

```
~/.copilot/session-state/<session-id>.jsonl
```

Beispiel:
```
~/.copilot/session-state/cli-1234.jsonl
```

### Verhalten

- Neue Sessions starten zunächst mit einer temporären ID (`untitled:xyz`)
- Sobald das SDK die Session anlegt, erhält sie eine echte ID (z. B. `cli-1234`)
- VS Code registriert einen Filesystem-Watcher auf dieses Verzeichnis – Änderungen triggern `onDidChangeSessions`

### Programmatischer Zugriff (Node.js)

```javascript
const fs = require('fs');
const path = require('path');
const os = require('os');

const sessionDir = path.join(os.homedir(), '.copilot', 'session-state');

const sessions = fs.readdirSync(sessionDir)
  .filter(f => f.endsWith('.jsonl'))
  .map(f => f.replace('.jsonl', ''));

console.log('Aktive Sessions:', sessions);
```

---

## Methode 4: Extension API – `toolInvocationToken` (für Extension-Entwickler)

Innerhalb einer VS Code Extension kann der `toolInvocationToken` aus dem `ChatRequest`-Objekt als eindeutiger Session-Identifier genutzt werden. Er stellt sicher, dass Tool-Invocations der richtigen Conversation zugeordnet werden.

> Ein direktes stabiles `sessionId`-Property auf `ChatRequest` existiert in der öffentlichen API noch nicht (Feature-Request: [Issue #202779](https://github.com/microsoft/vscode/issues/202779)). Der `toolInvocationToken` ist der empfohlene Workaround.

### Verwendung in TypeScript

```typescript
import * as vscode from 'vscode';

const handler: vscode.ChatRequestHandler = async (
  request: vscode.ChatRequest,
  context: vscode.ChatContext,
  stream: vscode.ChatResponseStream,
  token: vscode.CancellationToken
): Promise<vscode.ChatResult> => {

  // Opakes Token – eindeutig pro Conversation/Session
  const sessionToken = request.toolInvocationToken;

  // Session-State über ChatResult.metadata persistieren
  return {
    metadata: {
      sessionToken: sessionToken,
      // Eigene State-Daten hier speichern
    }
  };
};

// Im nächsten Turn aus ChatResponseTurn.result abrufen:
const previousState = context.history
  .filter(h => h instanceof vscode.ChatResponseTurn)
  .at(-1)
  ?.result?.metadata;
```

### Proposed API: `chatSessionsProvider`

Für Extension-Entwickler mit Preview-Features gibt es zusätzlich die **proposed API** `chatSessionsProvider` (`enabledApiProposals: ["chatSessionsProvider"]`), die einen `ChatSessionItemProvider` mit Session-Verwaltung ermöglicht. Diese API ist noch nicht finalisiert und kann sich ändern.

---

## Hinweise & Einschränkungen

- Das **Agent Debug Panel** ist nur für lokale Sessions verfügbar (nicht für Cloud Agents)
- Die **OTel-Integration** ist der einzige Weg, eine `session.id` in Echtzeit und maschinenlesbar zu erhalten
- Environment-Variablen haben immer Vorrang vor `settings.json`-Werten
- Dateien > 50 MB im Agent Debug Panel Import zeigen eine Warnung

---

## Weiterführende Links

- [VS Code 1.112 Release Notes](https://code.visualstudio.com/updates/v1_112)
- [Debug chat interactions (offizielle Doku)](https://code.visualstudio.com/docs/copilot/chat/chat-debug-view)
- [OTel Agent Monitoring (GitHub)](https://github.com/microsoft/vscode-copilot-chat/blob/main/docs/monitoring/agent_monitoring.md)
- [Chat Participant API](https://code.visualstudio.com/api/extension-guides/ai/chat)
- [Feature Request: Session ID in Chat API (Issue #202779)](https://github.com/microsoft/vscode/issues/202779)
