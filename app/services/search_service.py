import re
from sqlalchemy import or_, and_
from app.models import db, Document, Tag, Folder, User

class SearchService:
    @staticmethod
    def search_documents(
        query_str: str = "",
        category: str = None,
        tag_id: int = None,
        folder_id: int = None,
        is_starred: bool = None,
        user_id: int = None,
        current_user_id: int = None,
        include_deleted: bool = False,
        limit: int = 50
    ) -> list[dict]:
        """
        Executes a multi-criteria search and returns ranked document results with snippets.
        """
        query = Document.query

        if not include_deleted:
            query = query.filter(Document.is_deleted == False)

        if category and category != 'all':
            query = query.filter(Document.category == category)

        if tag_id:
            query = query.filter(Document.tags.any(Tag.id == tag_id))

        if folder_id is not None:
            query = query.filter(Document.folder_id == folder_id)

        if is_starred is not None:
            query = query.filter(Document.is_starred == is_starred)

        if user_id:
            query = query.filter(Document.user_id == user_id)

        results = []
        clean_q = query_str.strip() if query_str else ""

        if clean_q:
            tokens = [t.lower() for t in clean_q.split() if t]
            
            # Build filters for tokens
            token_filters = []
            for token in tokens:
                like_pattern = f"%{token}%"
                token_filters.append(
                    or_(
                        Document.title.ilike(like_pattern),
                        Document.description.ilike(like_pattern),
                        Document.filename.ilike(like_pattern),
                        Document.extracted_text.ilike(like_pattern),
                        Document.tags.any(Tag.name.ilike(like_pattern))
                    )
                )
            
            if token_filters:
                query = query.filter(and_(*token_filters))

            docs = query.order_by(Document.updated_at.desc()).limit(limit).all()

            for doc in docs:
                snippet = SearchService._generate_snippet(doc, tokens)
                doc_dict = doc.to_dict()
                doc_dict['search_snippet'] = snippet
                results.append(doc_dict)

        else:
            docs = query.order_by(Document.updated_at.desc()).limit(limit).all()
            for doc in docs:
                doc_dict = doc.to_dict()
                doc_dict['search_snippet'] = doc.description or ""
                results.append(doc_dict)

        return results

    @staticmethod
    def _generate_snippet(doc: Document, tokens: list[str]) -> str:
        """Generates a brief snippet highlighting matched tokens."""
        content = doc.extracted_text or doc.description or doc.title or ""
        if not content:
            return ""

        lower_content = content.lower()
        first_pos = -1

        for token in tokens:
            pos = lower_content.find(token)
            if pos != -1 and (first_pos == -1 or pos < first_pos):
                first_pos = pos

        if first_pos == -1:
            return content[:150] + ("..." if len(content) > 150 else "")

        start = max(0, first_pos - 60)
        end = min(len(content), first_pos + 120)
        snippet = content[start:end]

        if start > 0:
            snippet = "..." + snippet
        if end < len(content):
            snippet = snippet + "..."

        return snippet
