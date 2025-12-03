"""
Unit Tests untuk Git Compliance Checker System
Comprehensive test coverage untuk semua functionality
"""

import unittest
from git_validator import (
    TitleComplianceChecker,
    LinkExtractor,
    GitComplianceService,
    ComplianceStatus,
    ComplianceResult,
    ExtractedLinks
)


class TestTitleComplianceChecker(unittest.TestCase):
    """Test cases untuk TitleComplianceChecker"""
    
    def setUp(self):
        """Setup test fixtures"""
        self.checker = TitleComplianceChecker()
    
    def test_valid_title_basic(self):
        """Test title yang valid dengan format standar"""
        title = "feat: Tambah fitur login (Taiga #DATB-123)"
        result = self.checker.check_compliance(title)
        
        self.assertTrue(result.is_valid)
        self.assertEqual(result.status, ComplianceStatus.COMPLIANT)
        self.assertEqual(len(result.errors), 0)
        self.assertIsNotNone(result.parsed_data)
        self.assertEqual(result.parsed_data['type'], 'feat')
        self.assertEqual(result.parsed_data['summary'], 'Tambah fitur login')
        self.assertEqual(result.parsed_data['project'], 'DATB')
        self.assertEqual(result.parsed_data['ticket'], '123')
    
    def test_valid_title_all_types(self):
        """Test semua tipe commit yang valid"""
        valid_types = ['feat', 'fix', 'docs', 'style', 'refactor', 
                       'perf', 'test', 'chore', 'build', 'ci', 'revert']
        
        for commit_type in valid_types:
            title = f"{commit_type}: Update something important (Taiga #PROJ-999)"
            result = self.checker.check_compliance(title)
            
            self.assertTrue(result.is_valid, 
                          f"Type '{commit_type}' should be valid")
            self.assertEqual(result.parsed_data['type'], commit_type)
    
    def test_valid_title_case_insensitive(self):
        """Test case insensitive untuk format"""
        title = "FEAT: Update feature (taiga #datb-456)"
        result = self.checker.check_compliance(title)
        
        self.assertTrue(result.is_valid)
        self.assertEqual(result.parsed_data['type'], 'FEAT')
    
    def test_valid_title_with_numbers_in_project(self):
        """Test project name dengan angka"""
        title = "fix: Fix bug critical (Taiga #PROJ2024-789)"
        result = self.checker.check_compliance(title)
        
        self.assertTrue(result.is_valid)
        self.assertEqual(result.parsed_data['project'], 'PROJ2024')
    
    def test_invalid_title_empty(self):
        """Test title kosong"""
        result = self.checker.check_compliance("")
        
        self.assertFalse(result.is_valid)
        self.assertEqual(result.status, ComplianceStatus.NON_COMPLIANT)
        self.assertIn("tidak boleh kosong", result.errors[0].lower())
    
    def test_invalid_title_whitespace_only(self):
        """Test title hanya whitespace"""
        result = self.checker.check_compliance("   ")
        
        self.assertFalse(result.is_valid)
        self.assertIn("tidak boleh kosong", result.errors[0].lower())
    
    def test_invalid_title_wrong_type(self):
        """Test tipe commit yang tidak valid"""
        title = "invalid: Some changes (Taiga #PROJ-123)"
        result = self.checker.check_compliance(title)
        
        self.assertFalse(result.is_valid)
        self.assertTrue(any("tidak valid" in error.lower() for error in result.errors))
        self.assertTrue(len(result.suggestions) > 0)
    
    def test_invalid_title_missing_colon(self):
        """Test title tanpa colon"""
        title = "feat Tambah fitur (Taiga #PROJ-123)"
        result = self.checker.check_compliance(title)
        
        self.assertFalse(result.is_valid)
        self.assertTrue(any("tipe tidak ditemukan" in error.lower() 
                          for error in result.errors))
    
    def test_invalid_title_no_space_after_colon(self):
        """Test title tanpa spasi setelah colon"""
        title = "feat:Tambah fitur (Taiga #PROJ-123)"
        result = self.checker.check_compliance(title)
        
        self.assertFalse(result.is_valid)
        self.assertTrue(any("spasi" in error.lower() for error in result.errors))
    
    def test_invalid_title_missing_taiga_reference(self):
        """Test title tanpa referensi Taiga"""
        title = "feat: Tambah fitur baru"
        result = self.checker.check_compliance(title)
        
        self.assertFalse(result.is_valid)
        self.assertTrue(any("taiga" in error.lower() for error in result.errors))
        self.assertTrue(any("taiga" in suggestion.lower() 
                          for suggestion in result.suggestions))
    
    def test_invalid_title_wrong_taiga_format(self):
        """Test format Taiga yang salah"""
        invalid_formats = [
            "feat: Update (Taiga PROJ-123)",  # Missing #
            "feat: Update (Taiga #PROJ123)",  # Missing dash
            "feat: Update (Taiga #-123)",     # Missing project name
            "feat: Update (Taiga #PROJ-)",    # Missing ticket number
        ]
        
        for title in invalid_formats:
            result = self.checker.check_compliance(title)
            self.assertFalse(result.is_valid, 
                           f"Should be invalid: {title}")
    
    def test_invalid_title_summary_too_short(self):
        """Test ringkasan terlalu pendek"""
        title = "feat: Short (Taiga #PROJ-123)"
        result = self.checker.check_compliance(title)
        
        self.assertFalse(result.is_valid)
        self.assertTrue(any("terlalu pendek" in error.lower() 
                          for error in result.errors))
    
    def test_invalid_title_summary_too_long(self):
        """Test ringkasan terlalu panjang"""
        long_summary = "a" * 101
        title = f"feat: {long_summary} (Taiga #PROJ-123)"
        result = self.checker.check_compliance(title)
        
        self.assertFalse(result.is_valid)
        self.assertTrue(any("terlalu panjang" in error.lower() 
                          for error in result.errors))
    
    def test_suggestions_provided_for_errors(self):
        """Test bahwa setiap error memiliki suggestion"""
        invalid_titles = [
            "feat Tambah fitur",
            "invalid: Update (Taiga #PROJ-123)",
            "feat:NoSpace (Taiga #PROJ-123)",
            "feat: Update"
        ]
        
        for title in invalid_titles:
            result = self.checker.check_compliance(title)
            self.assertFalse(result.is_valid)
            self.assertGreater(len(result.suggestions), 0,
                             f"Should provide suggestions for: {title}")


class TestLinkExtractor(unittest.TestCase):
    """Test cases untuk LinkExtractor"""
    
    def setUp(self):
        """Setup test fixtures"""
        self.extractor = LinkExtractor()
    
    def test_extract_all_three_links(self):
        """Test ekstraksi semua 3 jenis link"""
        description = """
        Ticket Link: [(Taiga #DATB-10353)](https://projects.digitaltelkom.id/project/DATB/us/10353)
        Documentation Link: [Figma](https://www.figma.com/design/nzRdgZBt7kD8erOxqJZdtL/Dashboard)
        Testing Link: [https://testing.example.com/results/123]
        """
        
        result = self.extractor.extract_links(description)
        
        self.assertIsNotNone(result.ticket_link)
        self.assertIsNotNone(result.documentation_link)
        self.assertIsNotNone(result.testing_link)
        
        self.assertEqual(result.ticket_link, 
                        "https://projects.digitaltelkom.id/project/DATB/us/10353")
        self.assertIn("figma.com", result.documentation_link)
        self.assertIn("testing.example.com", result.testing_link)
    
    def test_extract_ticket_link_only(self):
        """Test ekstraksi hanya ticket link"""
        description = """
        Ticket Link: [(Taiga #DATB-123)](https://projects.digitaltelkom.id/project/DATB/us/123)
        """
        
        result = self.extractor.extract_links(description)
        
        self.assertIsNotNone(result.ticket_link)
        self.assertIsNone(result.documentation_link)
        self.assertIsNone(result.testing_link)
    
    def test_extract_documentation_link_only(self):
        """Test ekstraksi hanya documentation link"""
        description = """
        Documentation Link: [Figma Design](https://www.figma.com/file/abc123)
        """
        
        result = self.extractor.extract_links(description)
        
        self.assertIsNone(result.ticket_link)
        self.assertIsNotNone(result.documentation_link)
        self.assertIsNone(result.testing_link)
    
    def test_extract_testing_link_only(self):
        """Test ekstraksi hanya testing link"""
        description = """
        Testing Link: [https://www.postman.com/collection/xyz]
        """
        
        result = self.extractor.extract_links(description)
        
        self.assertIsNone(result.ticket_link)
        self.assertIsNone(result.documentation_link)
        self.assertIsNotNone(result.testing_link)
    
    def test_extract_empty_description(self):
        """Test dengan deskripsi kosong"""
        result = self.extractor.extract_links("")
        
        self.assertIsNone(result.ticket_link)
        self.assertIsNone(result.documentation_link)
        self.assertIsNone(result.testing_link)
    
    def test_extract_none_description(self):
        """Test dengan deskripsi None"""
        result = self.extractor.extract_links(None)
        
        self.assertIsNone(result.ticket_link)
        self.assertIsNone(result.documentation_link)
        self.assertIsNone(result.testing_link)
    
    def test_extract_case_insensitive(self):
        """Test ekstraksi case insensitive"""
        description = """
        TICKET LINK: [(Taiga #PROJ-1)](https://example.com/ticket/1)
        documentation link: [Docs](https://example.com/docs)
        TeStiNg LiNk: [https://example.com/test]
        """
        
        result = self.extractor.extract_links(description)
        
        self.assertIsNotNone(result.ticket_link)
        self.assertIsNotNone(result.documentation_link)
        self.assertIsNotNone(result.testing_link)
    
    # def test_extract_with_extra_whitespace(self):
    #     """Test ekstraksi dengan whitespace ekstra"""
    #     description = """
    #     Ticket Link:    [  (Taiga #PROJ-1)  ](  https://example.com/ticket  )
    #     Testing Link:    [  https://example.com/test  ]
    #     """
        
    #     result = self.extractor.extract_links(description)
        
    #     self.assertIsNotNone(result.ticket_link)
    #     self.assertIn("example.com/ticket", result.ticket_link)
    #     self.assertIsNotNone(result.testing_link)
    #     self.assertIn("example.com/test", result.testing_link)
    
    def test_extract_multiple_same_type_links(self):
        """Test jika ada multiple link dengan tipe sama (ambil yang pertama)"""
        description = """
        Ticket Link: [(Taiga #PROJ-1)](https://example.com/first)
        Ticket Link: [(Taiga #PROJ-2)](https://example.com/second)
        Testing Link: [https://example.com/test1]
        Testing Link: [https://example.com/test2]
        """
        
        result = self.extractor.extract_links(description)
        
        self.assertIsNotNone(result.ticket_link)
        self.assertIn("first", result.ticket_link)
        self.assertIsNotNone(result.testing_link)
        self.assertIn("test1", result.testing_link)
    
    def test_extract_urls_with_query_params(self):
        """Test URL dengan query parameters"""
        description = """
        Ticket Link: [(Taiga #PROJ-1)](https://example.com/page?id=123&type=task)
        """
        
        result = self.extractor.extract_links(description)
        
        self.assertIsNotNone(result.ticket_link)
        self.assertIn("id=123", result.ticket_link)
    
    def test_extract_urls_with_fragments(self):
        """Test URL dengan fragments (#)"""
        description = """
        Documentation Link: [Figma](https://figma.com/file/123#section-1)
        """
        
        result = self.extractor.extract_links(description)
        
        self.assertIsNotNone(result.documentation_link)
        self.assertIn("#section-1", result.documentation_link)
    
    def test_extract_all_links_fallback(self):
        """Test fallback method untuk ekstraksi semua URLs"""
        description = """
        Some text https://example.com/link1
        More text https://another.com/link2
        """
        
        all_links = self.extractor.extract_all_links(description)
        
        self.assertEqual(len(all_links), 2)
        self.assertIn("https://example.com/link1", all_links)
        self.assertIn("https://another.com/link2", all_links)
    
    def test_extract_no_markdown_format(self):
        """Test link tanpa format markdown (tidak ter-ekstrak)"""
        description = """
        Ticket Link: https://example.com/ticket
        Testing Link: https://example.com/test
        """
        
        result = self.extractor.extract_links(description)
        
        # Seharusnya None karena tidak dalam format yang benar
        # Ticket harus dalam [(text)](url), Testing harus dalam [url]
        self.assertIsNone(result.ticket_link)
        self.assertIsNone(result.testing_link)
    
    def test_testing_link_plain_url_format(self):
        """Test testing link dengan format plain URL dalam bracket"""
        description = """
        Testing Link: [https://testing.example.com/result/123]
        """
        
        result = self.extractor.extract_links(description)
        
        self.assertIsNotNone(result.testing_link)
        self.assertEqual(result.testing_link, "https://testing.example.com/result/123")
    
    def test_testing_link_with_query_params(self):
        """Test testing link dengan query parameters"""
        description = """
        Testing Link: [https://testing.example.com/result?id=123&type=integration]
        """
        
        result = self.extractor.extract_links(description)
        
        self.assertIsNotNone(result.testing_link)
        self.assertIn("id=123", result.testing_link)
        self.assertIn("type=integration", result.testing_link)
    
    def test_testing_link_with_fragment(self):
        """Test testing link dengan fragment"""
        description = """
        Testing Link: [https://docs.google.com/spreadsheets/d/abc123#section-1]
        """
        
        result = self.extractor.extract_links(description)
        
        self.assertIsNotNone(result.testing_link)
        self.assertIn("#section-1", result.testing_link)
    
    def test_mixed_link_formats(self):
        """Test kombinasi format link yang berbeda"""
        description = """
        Ticket Link: [(Taiga #PROJ-1)](https://taiga.example.com/project/1)
        Documentation Link: [Figma Design](https://figma.com/file/xyz)
        Testing Link: [https://postman.com/collection/abc]
        """
        
        result = self.extractor.extract_links(description)
        
        # Semua link harus ter-ekstrak dengan format masing-masing
        self.assertIsNotNone(result.ticket_link)
        self.assertIn("taiga.example.com", result.ticket_link)
        
        self.assertIsNotNone(result.documentation_link)
        self.assertIn("figma.com", result.documentation_link)
        
        self.assertIsNotNone(result.testing_link)
        self.assertIn("postman.com", result.testing_link)


class TestGitComplianceService(unittest.TestCase):
    """Test cases untuk GitComplianceService"""
    
    def setUp(self):
        """Setup test fixtures"""
        self.service = GitComplianceService()
    
    def test_check_commit_compliance_valid(self):
        """Test compliance check untuk commit yang valid"""
        title = "feat: Add new authentication feature (Taiga #AUTH-789)"
        result = self.service.check_commit_compliance(title)
        
        self.assertTrue(result.is_valid)
        self.assertEqual(result.status, ComplianceStatus.COMPLIANT)
    
    def test_check_commit_compliance_invalid(self):
        """Test compliance check untuk commit yang invalid"""
        title = "Added new feature"
        result = self.service.check_commit_compliance(title)
        
        self.assertFalse(result.is_valid)
        self.assertEqual(result.status, ComplianceStatus.NON_COMPLIANT)
        self.assertGreater(len(result.errors), 0)
    
    def test_check_mr_compliance_with_description(self):
        """Test compliance check MR dengan deskripsi"""
        mr_title = "fix: Resolve login bug (Taiga #BUG-456)"
        mr_description = """
        Ticket Link: [(Taiga #BUG-456)](https://projects.example.com/BUG-456)
        Documentation Link: [Docs](https://docs.example.com)
        Testing Link: [Tests](https://test.example.com)
        """
        
        result = self.service.check_mr_compliance(mr_title, mr_description)
        
        self.assertIn('compliance', result)
        self.assertIn('links', result)
        self.assertTrue(result['compliance'].is_valid)
        self.assertIsNotNone(result['links'].ticket_link)
    
    def test_check_mr_compliance_without_description(self):
        """Test compliance check MR tanpa deskripsi"""
        mr_title = "refactor: Improve code structure (Taiga #REF-123)"
        
        result = self.service.check_mr_compliance(mr_title)
        
        self.assertIn('compliance', result)
        self.assertIn('links', result)
        self.assertIsNone(result['links'])
    
    def test_format_compliance_report_valid(self):
        """Test format report untuk hasil yang valid"""
        title = "docs: Update API documentation (Taiga #DOCS-111)"
        result = self.service.check_commit_compliance(title)
        report = self.service.format_compliance_report(result)
        
        self.assertIn("COMPLIANT", report)
        self.assertIn("✓", report)
        self.assertIn("docs", report)
    
    def test_format_compliance_report_invalid(self):
        """Test format report untuk hasil yang invalid"""
        title = "update docs"
        result = self.service.check_commit_compliance(title)
        report = self.service.format_compliance_report(result)
        
        self.assertIn("NON-COMPLIANT", report)
        self.assertIn("✗", report)
        self.assertIn("Kesalahan:", report)
        self.assertIn("Saran", report)
    
    def test_integration_full_workflow(self):
        """Test integrasi full workflow dari input hingga output"""
        # Prepare data
        mr_title = "feat: Implement user dashboard (Taiga #DASH-999)"
        mr_description = """
        ## Description
        Implementing new user dashboard with analytics
        
        Ticket Link: [(Taiga #DASH-999)](https://projects.digitaltelkom.id/project/DASH/us/999)
        Documentation Link: [Text](https://www.figma.com/design/dashboard-design)
        Testing Link: [https://docs.google.com/spreadsheets/d/test-plan]
        
        ## Changes
        - Added dashboard component
        - Integrated analytics API
        """
        
        # Execute
        result = self.service.check_mr_compliance(mr_title, mr_description)
        
        # Assert compliance
        self.assertTrue(result['compliance'].is_valid)
        self.assertEqual(result['compliance'].status, ComplianceStatus.COMPLIANT)
        
        # Assert parsed data
        parsed = result['compliance'].parsed_data
        self.assertEqual(parsed['type'], 'feat')
        self.assertEqual(parsed['project'], 'DASH')
        self.assertEqual(parsed['ticket'], '999')
        
        # Assert extracted links
        links = result['links']
        self.assertIsNotNone(links.ticket_link)
        self.assertIn("digitaltelkom.id", links.ticket_link)
        self.assertIsNotNone(links.documentation_link)
        self.assertIn("figma.com", links.documentation_link)
        self.assertIsNotNone(links.testing_link)
        self.assertIn("google.com", links.testing_link)
        
        # Assert report generation
        report = self.service.format_compliance_report(result['compliance'])
        self.assertIn("COMPLIANT", report)


class TestEdgeCases(unittest.TestCase):
    """Test cases untuk edge cases dan corner cases"""
    
    def setUp(self):
        """Setup test fixtures"""
        self.service = GitComplianceService()
    
    def test_unicode_characters_in_title(self):
        """Test title dengan karakter unicode"""
        title = "feat: Tambah fitur notifikasi 🔔 (Taiga #NOTIF-123)"
        result = self.service.check_commit_compliance(title)
        
        # Should still validate the structure
        self.assertTrue(result.is_valid)
    
    def test_special_characters_in_summary(self):
        """Test special characters dalam summary"""
        title = "fix: Resolve issue with <script> tag & validation (Taiga #SEC-456)"
        result = self.service.check_commit_compliance(title)
        
        self.assertTrue(result.is_valid)
    
    def test_very_long_project_name(self):
        """Test project name yang sangat panjang"""
        title = "feat: New feature (Taiga #VERYLONGPROJECTNAME123-999)"
        result = self.service.check_commit_compliance(title)
        
        self.assertTrue(result.is_valid)
    
    def test_very_large_ticket_number(self):
        """Test ticket number yang sangat besar"""
        title = "fix: Bug fix critical issue (Taiga #PROJ-999999999)"
        result = self.service.check_commit_compliance(title)
        
        self.assertTrue(result.is_valid)
    
    def test_url_with_special_characters(self):
        """Test URL dengan special characters"""
        description = """
        Ticket Link: [(Taiga #PROJ-1)](https://example.com/path?param=value&other=test%20space)
        """
        extractor = LinkExtractor()
        result = extractor.extract_links(description)
        
        self.assertIsNotNone(result.ticket_link)
        self.assertIn("param=value", result.ticket_link)


def run_tests():
    """Run all tests with detailed output"""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test cases
    suite.addTests(loader.loadTestsFromTestCase(TestTitleComplianceChecker))
    suite.addTests(loader.loadTestsFromTestCase(TestLinkExtractor))
    suite.addTests(loader.loadTestsFromTestCase(TestGitComplianceService))
    suite.addTests(loader.loadTestsFromTestCase(TestEdgeCases))
    
    # Run tests with detailed output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print("=" * 70)
    
    return result


if __name__ == "__main__":
    run_tests()