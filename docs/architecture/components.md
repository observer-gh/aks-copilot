# Components

Inspector: Parses manifests and finds Violation objects.

Thinker: Receives Violation objects and generates PatchOperation objects using rules and the LLM.

Patcher: Applies PatchOperations to produce the final, patched manifests.

Reporter: Generates reports, triggers deployment, and sends notifications.
