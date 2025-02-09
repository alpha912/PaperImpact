from colorama import init, Fore, Style, Back
import pandas as pd  # Add this import
import time
from typing import Dict, Any, List

class PrettyLogger:
    def __init__(self, log_file=None):
        """Initialize with optional file logging"""
        init()
        self.log_file = log_file
        if log_file:
            self.file_handler = open(log_file, 'a', encoding='utf-8')
    
    def _write_log(self, text: str):
        """Write to log file if enabled"""
        if self.log_file and hasattr(self, 'file_handler'):
            timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
            self.file_handler.write(f"[{timestamp}] {text}\n")
            self.file_handler.flush()
        
    def __del__(self):
        """Cleanup file handler"""
        if hasattr(self, 'file_handler'):
            self.file_handler.close()
        
    def header(self, text: str):
        """Print a beautiful header with borders"""
        width = 60
        print(f"\n{Fore.CYAN}{'='*width}")
        print(f"{text.center(width)}")
        print(f"{'='*width}{Style.RESET_ALL}")
        
    def section(self, text: str):
        """Print a section header"""
        print(f"\n{Fore.BLUE}▶ {text}{Style.RESET_ALL}")
        
    def progress(self, text: str):
        """Print a progress message"""
        print(f"{Fore.GREEN}→ {text}...{Style.RESET_ALL}")
        
    def success(self, text: str):
        """Print a success message"""
        print(f"{Fore.GREEN}✓ {text}{Style.RESET_ALL}")
        
    def info(self, text: str):
        """Print an info message"""
        print(f"{Fore.BLUE}ℹ {text}{Style.RESET_ALL}")
        
    def warning(self, text: str):
        """Print a warning message"""
        print(f"{Fore.YELLOW}⚠ {text}{Style.RESET_ALL}")
        
    def error(self, text: str):
        """Enhanced error logging"""
        message = f"{Fore.RED}✖ ERROR: {text}{Style.RESET_ALL}"
        print(message)
        self._write_log(f"ERROR: {text}")
        
    def validation_step(self, text: str):
        """Print a validation step message"""
        print(f"{Fore.CYAN}🔍 {text}...{Style.RESET_ALL}")
        
    def validation_result(self, text: str):
        """Print a validation result message"""
        print(f"{Fore.MAGENTA}   └─ {text}{Style.RESET_ALL}")

    def validation_summary(self, stats: Dict[str, Any]):
        """Print validation summary"""
        print(f"\n{Fore.CYAN}📋 Validation Summary:{Style.RESET_ALL}")
        print(f"   Total papers analyzed: {stats['total_papers']:,}")
        print(f"   Valid papers: {stats['valid_papers']:,}")
        print(f"   Papers with warnings: {stats['papers_with_warnings']:,}")
        print(f"   Invalid papers: {stats['invalid_papers']:,}")
        if stats['invalid_papers'] > 0:
            print(f"   Common issues: {', '.join(stats['common_issues'])}")
        
    def print_stats(self, country: str, stats: Dict[str, Any]):
        """Print publication statistics for a country"""
        try:
            max_label_length = 45  # Fixed width for better alignment
            total_papers = int(stats.get('total_papers', 0))
            
            print(f"\n{Fore.CYAN}📊 Statistics for {str(country).upper()}{Style.RESET_ALL}")
            
            # Basic stats with enhanced details
            print(f"   {'Total papers'.ljust(max_label_length)} │ {total_papers:,}")
            print(f"   {'Average impact score'.ljust(max_label_length)} │ {Fore.YELLOW}{float(stats.get('avg_impact_score', 0)):.2f} / 100{Style.RESET_ALL}")
            
            # Highest scoring paper details with improved formatting
            print(f"\n   {'Highest impact paper'.ljust(max_label_length)} │ {Fore.GREEN}{float(stats.get('highest_score', 0)):.2f}{Style.RESET_ALL}")
            print(f"   {Fore.CYAN}└─{Style.RESET_ALL} Journal: {stats.get('highest_score_journal', 'N/A')}")
            print(f"   {Fore.CYAN}└─{Style.RESET_ALL} Title: {stats.get('highest_score_paper_title', 'N/A')[:100]}...")
            print(f"   {Fore.CYAN}└─{Style.RESET_ALL} DOI: {stats.get('highest_score_paper_doi', 'N/A')}")
            
            # Lowest scoring paper details with improved formatting
            print(f"\n   {'Lowest impact paper'.ljust(max_label_length)} │ {Fore.RED}{float(stats.get('lowest_score', 0)):.2f}{Style.RESET_ALL}")
            print(f"   {Fore.CYAN}└─{Style.RESET_ALL} Journal: {stats.get('lowest_score_journal', 'N/A')}")
            print(f"   {Fore.CYAN}└─{Style.RESET_ALL} Title: {stats.get('lowest_score_paper_title', 'N/A')[:100]}...")
            print(f"   {Fore.CYAN}└─{Style.RESET_ALL} DOI: {stats.get('lowest_score_paper_doi', 'N/A')}")
            
            print("\n   Impact Distribution:")
            
            # Calculate percentages and bars for impact tiers
            very_high = int(stats.get('very_high_impact_papers', 0))
            high = int(stats.get('high_impact_papers', 0))
            medium = int(stats.get('medium_impact_papers', 0))
            low = int(stats.get('low_impact_papers', 0))
            very_low = int(stats.get('very_low_impact_papers', 0))
            
            bar_width = 40  # Width of the bar in characters
            
            def print_tier_bar(label: str, count: int, color: str):
                percentage = (count / total_papers) * 100
                bar_length = int((count / total_papers) * bar_width)
                bar = '█' * bar_length
                spaces = ' ' * (bar_width - bar_length)
                # Color the entire line including label and count
                print(f"{color}   {label.ljust(max_label_length)} │ {bar}{spaces} {count:,} ({percentage:.1f}%){Style.RESET_ALL}")
            
            print_tier_bar("★★★★★ Very High impact papers (80-100)", very_high, Fore.BLUE)
            print_tier_bar("★★★★☆ High impact papers (60-80)", high, Fore.GREEN)
            print_tier_bar("★★★☆☆ Medium impact papers (40-60)", medium, Fore.YELLOW)
            print_tier_bar("★★☆☆☆ Low impact papers (20-40)", low, Fore.RED)
            print_tier_bar("★☆☆☆☆ Very Low impact papers (0-20)", very_low, Fore.RED)
            
            # Scale line with label "Total Papers"
            print(f"{Fore.WHITE}   {'Scale (Total Papers)'.ljust(max_label_length)} │ {'▔' * bar_width} {total_papers:,} (100%){Style.RESET_ALL}")
            
            # International collaboration percentage
            collab_pct = float(stats.get('international_collab_pct', 0))
            bar_length = int((collab_pct / 100) * bar_width)
            collab_bar = '█' * bar_length + ' ' * (bar_width - bar_length)
            print(f"\n{Fore.CYAN}   {'International collaborations'.ljust(max_label_length)} │ {collab_bar} {collab_pct:.1f}%{Style.RESET_ALL}")
            
        except (KeyError, ValueError, TypeError) as e:
            print(f"{Fore.RED}Error displaying stats: {str(e)}{Style.RESET_ALL}")
            self._write_log(f"Error displaying stats: {str(e)}")
        
    def print_journal_distribution(self, journal_stats: Dict[str, int], max_show: int = 10, scimago_ranks: Dict[str, int] = None):
        """Print top journals distribution with SCImago ranks"""
        if not journal_stats:
            self.warning("No journal distribution data available")
            return

        # Increase rank width and use proper padding
        rank_width = 12  # Width for rank display "(   XXXXX   )"
        journal_width = 40
        
        print(f"\n{Fore.CYAN}📚 Top Journals:{Style.RESET_ALL}")
        for journal, count in list(sorted(journal_stats.items(), key=lambda x: x[1], reverse=True))[:max_show]:
            bar_length = int((count / max(journal_stats.values())) * 30)
            bar = '█' * bar_length
            
            # Format rank with consistent padding and alignment
            if scimago_ranks and journal in scimago_ranks:
                rank = scimago_ranks.get(journal)
                if rank is not None:
                    # Right-align the rank number with fixed width
                    rank_str = f"{Fore.YELLOW}({str(rank).rjust(10)}){Style.RESET_ALL}"
                else:
                    rank_str = f"{Fore.YELLOW}({'N/A'.rjust(10)}){Style.RESET_ALL}"
            else:
                rank_str = f"{Fore.YELLOW}({'N/A'.rjust(10)}){Style.RESET_ALL}"
            
            # Print with fixed widths for consistent alignment
            print(f"   {rank_str} {journal[:journal_width].ljust(journal_width)} │ {bar} ({count})")

    def print_year_distribution(self, years: Dict[int, int]):
        """Print publication years distribution"""
        print(f"\n{Fore.CYAN}📈 Publication Years:{Style.RESET_ALL}")
        max_count = max(years.values())
        for year in sorted(years.keys()):
            count = years[year]
            bar_length = int((count / max_count) * 30)
            bar = '█' * bar_length
            print(f"   {str(year).ljust(6)} │ {bar} ({count})")
            
    def print_comparison(self, countries: List[Dict[str, Any]]):
        """Print comparison between countries"""
        max_papers = max(c['total_papers'] for c in countries)
        max_impact = max(c['avg_impact_score'] for c in countries)
        
        print(f"\n{Fore.CYAN}🌍 Country Comparison{Style.RESET_ALL}")
        for country in sorted(countries, key=lambda x: x['total_papers'], reverse=True):
            papers_bar = '█' * int((country['total_papers'] / max_papers) * 20)
            impact_bar = '█' * int((country['avg_impact_score'] / max_impact) * 20)
            print(f"\n   {country['name'].upper()}")
            print(f"   Papers:    {papers_bar} ({country['total_papers']:,})")
            print(f"   Impact:    {impact_bar} ({country['avg_impact_score']:.2f})")
        for country in sorted(countries, key=lambda x: x['total_papers'], reverse=True):
            print(f"   Int'l:     {country['international_collab_pct']:.1f}%")
            papers_bar = '█' * int((country['total_papers'] / max_papers) * 20)
            impact_bar = '█' * int((country['avg_impact_score'] / max_impact) * 20)
            print(f"\n   {country['name'].upper()}")
            print(f"   Papers:    {papers_bar} ({country['total_papers']:,})")
            print(f"   Impact:    {impact_bar} ({country['avg_impact_score']:.2f})")
            print(f"   Int'l:     {country['international_collab_pct']:.1f}%")