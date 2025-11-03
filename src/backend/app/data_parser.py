import pandas as pd
import re

class DataParser:
    def __init__(self):
        self.df = None

    def normalize_text(self, text: str) -> str:
        if not text:
            return ""

        text = text.lower()

        # Remove common placeholder / missing info strings
        ignore_strings = [
            "no board service info",
            "no employment information provided",
            "no info available",
            "no employment/military info in database",
            "retired",
            "(retired)",
            "no employment info",
            "no board service information provided",
            "no known board roles",
            "no publicly known board positions",
            "no board affiliations found.",
            "no board service identified",
            "no formal board service identified",
            "no professional information",
            "no board roles identified",
            "no explicit board memberships found",
            "no information found",
            "no information found - refers to facilities not a person",
            "nonprofit: none"
        ]

        # Replace any placeholder string with empty string
        for s in ignore_strings:
            text = text.replace(s, "")

        # Remove HTML line breaks
        text = re.sub(r"<br\s*/?>", " ", text)

        # Remove common org suffixes
        text = re.sub(r"\b(inc|corp|corporation|ltd|llc|co|company|foundation|institute|university|college|academy|association|group|holdings)\b", " ", text)

        # Remove generic titles / board roles
        text = re.sub(r"\b(ceo|cfo|coo|president|chair|director|member|trustee|secretary|treasurer|advisor|officer|researcher|managing director)\b", " ", text)

        # Remove stopwords
        text = re.sub(r"\b(the|of|and|a|an|for|in|on|at|by|with)\b", " ", text)

        # Remove years
        text = re.sub(r"\d{4}\s*-\s*(\d{4}|present)", " ", text)

        # Remove other punctuation
        text = re.sub(r"[^\w\s]", " ", text)

        # Collapse multiple spaces
        text = re.sub(r"\s+", " ", text).strip()

        return text

    def parse_excel(self, file_path: str):
        """Parse Excel file from disk."""
        self.df = pd.read_excel(file_path)
        return self._process_dataframe()

    def parse_excel_bytes(self, file_bytes):
        """Parse Excel file from uploaded bytes."""
        self.df = pd.read_excel(file_bytes)
        return self._process_dataframe()

    def _process_dataframe(self):
        """Internal method to process the dataframe after loading."""
        self.df = self.df.rename(columns={
            'Name': 'name',
            'Professional Title/Employment & Career': 'employment',
            'Board Service': 'board_service'
        })

        self.df = self.df.fillna('')

        self.df['employment_norm'] = self.df['employment'].apply(self.normalize_text)
        self.df['board_service_norm'] = self.df['board_service'].apply(self.normalize_text)

        return self.df