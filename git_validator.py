"""
Git Compliance Checker System
Sistem untuk monitoring compliance commits & merge requests
"""

import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class ComplianceStatus(Enum):
    """Status compliance checking"""
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"


@dataclass
class ComplianceResult:
    """Result dari compliance checking"""
    status: ComplianceStatus
    is_valid: bool
    errors: List[str]
    suggestions: List[str]
    parsed_data: Optional[Dict[str, str]] = None


@dataclass
class ExtractedLinks:
    """Hasil ekstraksi links dari deskripsi"""
    ticket_link: Optional[str] = None
    documentation_link: Optional[str] = None
    testing_link: Optional[str] = None


class TitleComplianceChecker:
    """
    Checker untuk validasi title commit/MR sesuai format:
    <tipe>: <ringkasan singkat> (Taiga #<NamaProject>-<NomorTicket>)
    """
    
    # Tipe-tipe commit yang umum digunakan
    VALID_TYPES = [
        'feat', 'fix', 'docs', 'style', 'refactor', 
        'perf', 'test', 'chore', 'build', 'ci', 'revert'
    ]
    
    # Pattern untuk validasi format lengkap
    TITLE_PATTERN = re.compile(
        r'^(?P<type>[a-z]+):\s+(?P<summary>.+?)\s+\(Taiga\s+#(?P<project>[A-Z0-9]+)-(?P<ticket>\d+)\)$',
        re.IGNORECASE
    )
    
    def check_compliance(self, title: str) -> ComplianceResult:
        """
        Melakukan checking compliance terhadap title
        
        Args:
            title: Title commit atau merge request
            
        Returns:
            ComplianceResult dengan detail validasi
        """
        errors = []
        suggestions = []
        parsed_data = None
        
        # Cek jika title kosong
        if not title or not title.strip():
            errors.append("Title tidak boleh kosong")
            suggestions.append("Gunakan format: <tipe>: <ringkasan singkat> (Taiga #<NamaProject>-<NomorTicket>)")
            return ComplianceResult(
                status=ComplianceStatus.NON_COMPLIANT,
                is_valid=False,
                errors=errors,
                suggestions=suggestions
            )
        
        title = title.strip()
        
        # Cek format menggunakan regex
        match = self.TITLE_PATTERN.match(title)
        
        if not match:
            # Analisa kesalahan spesifik
            errors, suggestions = self._analyze_errors(title)
            return ComplianceResult(
                status=ComplianceStatus.NON_COMPLIANT,
                is_valid=False,
                errors=errors,
                suggestions=suggestions
            )
        
        # Ekstrak data
        parsed_data = match.groupdict()
        commit_type = parsed_data['type'].lower()
        
        # Validasi tipe commit
        if commit_type not in self.VALID_TYPES:
            errors.append(f"Tipe commit '{commit_type}' tidak valid")
            suggestions.append(f"Gunakan salah satu tipe: {', '.join(self.VALID_TYPES)}")
            return ComplianceResult(
                status=ComplianceStatus.NON_COMPLIANT,
                is_valid=False,
                errors=errors,
                suggestions=suggestions,
                parsed_data=parsed_data
            )
        
        # Validasi panjang summary
        summary = parsed_data['summary'].strip()
        if len(summary) < 10:
            errors.append("Ringkasan terlalu pendek (minimal 10 karakter)")
            suggestions.append("Berikan deskripsi yang lebih detail tentang perubahan")
        
        if len(summary) > 100:
            errors.append("Ringkasan terlalu panjang (maksimal 100 karakter)")
            suggestions.append("Ringkas deskripsi menjadi lebih singkat dan jelas")
        
        # Jika ada error, return non-compliant
        if errors:
            return ComplianceResult(
                status=ComplianceStatus.NON_COMPLIANT,
                is_valid=False,
                errors=errors,
                suggestions=suggestions,
                parsed_data=parsed_data
            )
        
        # Semua validasi passed
        return ComplianceResult(
            status=ComplianceStatus.COMPLIANT,
            is_valid=True,
            errors=[],
            suggestions=[],
            parsed_data=parsed_data
        )
    
    def _analyze_errors(self, title: str) -> Tuple[List[str], List[str]]:
        """Menganalisa kesalahan spesifik dalam title"""
        errors = []
        suggestions = []
        
        # Cek apakah ada tipe di awal
        if not re.match(r'^[a-z]+:', title, re.IGNORECASE):
            errors.append("Format tipe tidak ditemukan di awal title")
            suggestions.append("Mulai title dengan '<tipe>:' (contoh: feat:, fix:, docs:)")
        else:
            # Ekstrak tipe yang digunakan
            type_match = re.match(r'^([a-z]+):', title, re.IGNORECASE)
            if type_match:
                used_type = type_match.group(1).lower()
                if used_type not in self.VALID_TYPES:
                    errors.append(f"Tipe '{used_type}' tidak valid")
                    suggestions.append(f"Gunakan salah satu tipe: {', '.join(self.VALID_TYPES)}")
        
        # Cek apakah ada spasi setelah colon
        if re.match(r'^[a-z]+:[^\s]', title, re.IGNORECASE):
            errors.append("Tidak ada spasi setelah tanda titik dua (:)")
            suggestions.append("Tambahkan spasi setelah ':' (contoh: 'feat: ' bukan 'feat:')")
        
        # Cek apakah ada referensi Taiga
        if 'Taiga' not in title and 'taiga' not in title.lower():
            errors.append("Referensi Taiga tidak ditemukan")
            suggestions.append("Tambahkan '(Taiga #<NamaProject>-<NomorTicket>)' di akhir title")
        else:
            # Cek format Taiga
            if not re.search(r'\(Taiga\s+#[A-Z0-9]+-\d+\)', title, re.IGNORECASE):
                errors.append("Format referensi Taiga tidak sesuai")
                suggestions.append("Gunakan format: (Taiga #<NamaProject>-<NomorTicket>), contoh: (Taiga #DATB-123)")
        
        # Jika tidak ada error spesifik, berikan saran umum
        if not errors:
            errors.append("Format title tidak sesuai dengan standar")
            suggestions.append("Format yang benar: <tipe>: <ringkasan singkat> (Taiga #<NamaProject>-<NomorTicket>)")
            suggestions.append("Contoh: feat: Tambah fitur login (Taiga #DATB-123)")
        
        return errors, suggestions


class LinkExtractor:
    """
    Extractor untuk mengambil link dari deskripsi MR/commit
    Format yang diharapkan:
    - Ticket Link: [(Taiga #<Project>-<Number>)](url)
    - Documentation Link: [Figma](url)
    - Testing Link: [url]
    """
    
    # Pattern untuk ekstraksi markdown links
    TICKET_LINK_PATTERN = re.compile(
        r'Ticket\s+Link:\s*\[(?:[^\]]+)\]\((?P<url>https?://[^\)]+)\)',
        re.IGNORECASE
    )
    
    DOCUMENTATION_LINK_PATTERN = re.compile(
        r'Documentation\s+Link:\s*\[(?:[^\]]+)\]\((?P<url>https?://[^\)]+)\)',
        re.IGNORECASE
    )
    
    TESTING_LINK_PATTERN = re.compile(
        r'Testing\s+Link:\s*\[(?P<url>https?://[^\]]+)\]',
        re.IGNORECASE
    )
    
    def extract_links(self, description: str) -> ExtractedLinks:
        """
        Ekstrak semua links dari deskripsi
        
        Args:
            description: Deskripsi dari MR atau commit
            
        Returns:
            ExtractedLinks object dengan semua links yang ditemukan
        """
        if not description:
            return ExtractedLinks()
        
        ticket_link = None
        documentation_link = None
        testing_link = None
        
        # Extract Ticket Link
        ticket_match = self.TICKET_LINK_PATTERN.search(description)
        if ticket_match:
            ticket_link = ticket_match.group('url').strip()
        
        # Extract Documentation Link
        doc_match = self.DOCUMENTATION_LINK_PATTERN.search(description)
        if doc_match:
            documentation_link = doc_match.group('url').strip()
        
        # Extract Testing Link
        testing_match = self.TESTING_LINK_PATTERN.search(description)
        if testing_match:
            testing_link = testing_match.group('url').strip()
        
        return ExtractedLinks(
            ticket_link=ticket_link,
            documentation_link=documentation_link,
            testing_link=testing_link
        )
    
    def extract_all_links(self, description: str) -> List[str]:
        """
        Ekstrak semua URLs dari deskripsi (fallback method)
        
        Args:
            description: Deskripsi dari MR atau commit
            
        Returns:
            List of URLs found
        """
        if not description:
            return []
        
        # Pattern untuk menangkap URL umum
        url_pattern = re.compile(r'https?://[^\s\)]+')
        return url_pattern.findall(description)


class GitComplianceService:
    """
    Service utama untuk monitoring compliance
    """
    
    def __init__(self):
        self.title_checker = TitleComplianceChecker()
        self.link_extractor = LinkExtractor()
    
    def check_commit_compliance(self, commit_title: str) -> ComplianceResult:
        """Check compliance untuk commit"""
        return self.title_checker.check_compliance(commit_title)
    
    def check_mr_compliance(self, mr_title: str, mr_description: str = None) -> Dict:
        """
        Check compliance untuk merge request
        
        Args:
            mr_title: Title dari MR
            mr_description: Deskripsi dari MR (optional)
            
        Returns:
            Dictionary dengan hasil compliance dan extracted links
        """
        compliance_result = self.title_checker.check_compliance(mr_title)
        
        extracted_links = None
        if mr_description:
            extracted_links = self.link_extractor.extract_links(mr_description)
        
        return {
            'compliance': compliance_result,
            'links': extracted_links
        }
    
    def format_compliance_report(self, result: ComplianceResult, use_unicode: bool = True) -> str:
        """
        Format hasil compliance menjadi report yang readable
        
        Args:
            result: ComplianceResult object
            use_unicode: Use unicode symbols (default True, set False for Windows console)
            
        Returns:
            Formatted string report
        """
        report_lines = []
        
        # Symbols for different environments
        if use_unicode:
            check_mark = "✓"
            cross_mark = "✗"
        else:
            check_mark = "[OK]"
            cross_mark = "[X]"
        
        if result.is_valid:
            report_lines.append(f"{check_mark} COMPLIANT - Title sudah sesuai standar")
            if result.parsed_data:
                report_lines.append(f"  Tipe: {result.parsed_data['type']}")
                report_lines.append(f"  Ringkasan: {result.parsed_data['summary']}")
                report_lines.append(f"  Project: {result.parsed_data['project']}")
                report_lines.append(f"  Ticket: {result.parsed_data['ticket']}")
        else:
            report_lines.append(f"{cross_mark} NON-COMPLIANT - Title tidak sesuai standar")
            report_lines.append("\nKesalahan:")
            for error in result.errors:
                report_lines.append(f"  - {error}")
            
            if result.suggestions:
                report_lines.append("\nSaran Perbaikan:")
                for suggestion in result.suggestions:
                    report_lines.append(f"  - {suggestion}")
        
        return "\n".join(report_lines)


# Example usage
if __name__ == "__main__":
    import sys
    import os
    
    # Fix Windows console encoding
    if sys.platform == 'win32':
        # Set console to UTF-8
        if sys.stdout.encoding != 'utf-8':
            sys.stdout.reconfigure(encoding='utf-8')
    
    service = GitComplianceService()
    
    # Detect if Unicode is supported
    use_unicode = True
    try:
        sys.stdout.write('\u2713')
        sys.stdout.flush()
    except (UnicodeEncodeError, AttributeError):
        use_unicode = False
    
    # Test valid title
    print("=" * 60)
    print("Test 1: Valid Title")
    print("=" * 60)
    valid_title = "feat: Tambah fitur authentication (Taiga #DATB-123)"
    result = service.check_commit_compliance(valid_title)
    print(service.format_compliance_report(result, use_unicode=use_unicode))
    
    # Test invalid title
    print("\n" + "=" * 60)
    print("Test 2: Invalid Title - Missing Taiga Reference")
    print("=" * 60)
    invalid_title = "feat: Tambah fitur authentication"
    result = service.check_commit_compliance(invalid_title)
    print(service.format_compliance_report(result, use_unicode=use_unicode))
    
    # Test MR with description
    print("\n" + "=" * 60)
    print("Test 3: MR with Links Extraction")
    print("=" * 60)
    mr_title = "fix: Perbaiki bug login (Taiga #DATB-456)"
    mr_description = """
    Ticket Link: [(Taiga #DATB-456)](https://projects.digitaltelkom.id/project/DATB/us/10353)
    Documentation Link: [Figma](https://www.figma.com/design/nzRdgZBt7kD8erOxqJZdtL/Dashboard-Monitoring-Git)
    Testing Link: [https://testing.example.com/result/123]
    """
    result = service.check_mr_compliance(mr_title, mr_description)
    print(service.format_compliance_report(result['compliance'], use_unicode=use_unicode))
    print("\nExtracted Links:")
    links = result['links']
    print(f"  Ticket: {links.ticket_link}")
    print(f"  Documentation: {links.documentation_link}")
    print(f"  Testing: {links.testing_link}")