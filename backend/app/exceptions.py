class DuplicateDocumentError(Exception):
    """
    Raised when an uploaded document already exists in the registry based on its checksum.
    
    Attributes:
        document_id (str): The unique identifier of the existing document in the registry.
    """

    def __init__(self, document_id: str):
        self.document_id: str = document_id
        super().__init__(f"Duplicate document: {document_id}")
