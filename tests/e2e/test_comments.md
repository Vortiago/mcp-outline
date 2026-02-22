```mermaid
flowchart TD
    CD[create_document] --> AC[add_comment]
    AC --> LC[list_document_comments]
    LC --> GC[get_comment]

    CDA[create_document A\nBacklink Target] --> CDB[create_document B\nlinks to A]
    CDB --> BL[get_document_backlinks\nfor A]
```
