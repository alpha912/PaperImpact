import os
import sys
import argparse
import pandas as pd
import numpy as np
from datetime import datetime
from collections import defaultdict
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Tuple, Any
from src.logger import PrettyLogger
from tqdm import tqdm  # Add this import
import glob

class JournalImpactAnalyzer:
    def __init__(self, scimago_path: str, logger: PrettyLogger):
        """
        Initialize with validation
        """
        if not os.path.exists(scimago_path):
            raise FileNotFoundError(f"SCImago data file not found: {scimago_path}")
        
        self.logger = logger
        try:
            self.scimago_df = self._load_scimago_data(scimago_path)
        except Exception as e:
            raise RuntimeError(f"Failed to initialize analyzer: {str(e)}")
        
        # Set up scoring weights
        self.weights = {
            'journal_impact': 0.30,    # Journal prestige and impact factor
            'citation_impact': 0.30,   # Citation count relative to field
            'recency': 0.15,          # More recent papers score higher
            'volume': 0.15,           # Contribution to field
            'collaboration': 0.10      # International collaboration
        }
        
        # Add journal ranks dictionary
        self.journal_ranks = {}
        if 'Rank' in self.scimago_df.columns:
            self.journal_ranks = dict(zip(self.scimago_df['Title'], self.scimago_df['Rank']))
        
        self.global_max_citations = 0
        self.global_top_cited_paper = None
        self.global_top_journal = None
        self.global_journal_papers = defaultdict(list)
    
    def _load_scimago_data(self, path: str) -> pd.DataFrame:
        """Load and prepare SCImago journal rankings data"""
        self.logger.progress("Loading SCImago data")
        try:
            df = pd.read_csv(path, 
                            sep=None,  # Auto-detect separator
                            engine='python',
                            on_bad_lines='skip')  # Skip problematic lines
            
            # Clean SJR scores - handle potential missing columns
            if 'SJR' in df.columns:
                df['SJR'] = pd.to_numeric(
                    df['SJR'].astype(str).str.replace(',', '.'), 
                    errors='coerce'
                ).fillna(0)
            else:
                self.logger.warning("SJR column not found in data")
                df['SJR'] = 0
                
            if 'H index' in df.columns:
                df['H index'] = pd.to_numeric(df['H index'], errors='coerce').fillna(0)
            else:
                self.logger.warning("H index column not found in data")
                df['H index'] = 0
            
            # Create clean titles for matching
            df['clean_title'] = df['Title'].str.lower().str.strip()
            self.logger.success(f"Loaded {len(df)} journal entries from SCImago")
            return df
            
        except Exception as e:
            self.logger.error(f"Error loading SCImago data: {str(e)}")
            raise RuntimeError(f"Failed to load SCImago data: {str(e)}")
    
    def match_journal(self, title: str, issn: str = None) -> pd.Series:
        """Match a journal with SCImago database using title and ISSN"""
        if issn and isinstance(issn, str):
            # Try exact ISSN match first
            issn_match = self.scimago_df[self.scimago_df['Issn'].str.contains(issn, na=False, regex=False)]
            if not issn_match.empty:
                return issn_match.iloc[0]
        
        # Clean title for matching
        clean_title = str(title).lower().strip()
        
        # Try exact match
        exact_match = self.scimago_df[self.scimago_df['clean_title'] == clean_title]
        if not exact_match.empty:
            return exact_match.iloc[0]
        
        # Try partial match with regex=False to prevent warning
        partial_matches = self.scimago_df[self.scimago_df['clean_title'].str.contains(
            clean_title, 
            na=False, 
            regex=False  # Add this parameter to prevent regex interpretation
        )]
        if not partial_matches.empty:
            return partial_matches.iloc[0]
        
        return None
    
    def process_papers(self, papers_path: str) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Enhanced paper processing with validation and progress tracking
        """
        if not os.path.exists(papers_path):
            raise FileNotFoundError(f"Papers file not found: {papers_path}")
        
        # Read CSV with low_memory=False to prevent dtype warnings
        df = pd.read_csv(papers_path, encoding='utf-8', low_memory=False)
        
        # Update column mapping to match actual CSV structure
        column_mapping = {
            'Source title': 'journal_title',
            'ISSN': 'issn',
            'Year': 'year',
            'Cited by': 'citation_count',
            'Affiliations': 'affiliations',
            'Open Access': 'open_access',
            'Document Type': 'document_type',
            'Title': 'title',
            'DOI': 'doi',
            'Authors': 'authors',
            'Publisher': 'publisher'
        }
        
        # Debug info for column names
        self.logger.info(f"Available columns: {', '.join(df.columns)}")
        
        # Rename columns that exist in the dataframe
        existing_columns = {k: v for k, v in column_mapping.items() if k in df.columns}
        df = df.rename(columns=existing_columns)
        
        # Check if required columns exist under different names
        if 'journal_title' not in df.columns and 'Source title' in df.columns:
            df['journal_title'] = df['Source title']
        if 'year' not in df.columns and 'Year' in df.columns:
            df['year'] = df['Year']
            
        # Validate required columns
        required_columns = ['journal_title', 'year']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")
        
        # Validate data types
        df['year'] = pd.to_numeric(df['year'], errors='coerce')
        df['citation_count'] = pd.to_numeric(df['citation_count'], errors='coerce').fillna(0)
        
        # Remove invalid years
        current_year = datetime.now().year
        df = df[df['year'].between(1900, current_year)]
        
        # Initialize score components
        scores = pd.DataFrame(index=df.index)
        
        # Initialize validation stats
        validation_stats = {
            'total_papers': len(df),
            'valid_papers': 0,
            'papers_with_warnings': 0,
            'invalid_papers': 0,
            'common_issues': []
        }

        # Validate data
        self.logger.validation_step("Checking required columns")
        missing_cols = [col for col in required_columns if col not in df.columns]
        if missing_cols:
            self.logger.validation_result(f"Missing columns: {', '.join(missing_cols)}")
            validation_stats['common_issues'].append('missing_required_columns')
        else:
            self.logger.validation_result("All required columns present")

        self.logger.validation_step("Validating publication years")
        invalid_years = df[~df['year'].between(1900, current_year)].shape[0]
        if invalid_years > 0:
            self.logger.validation_result(f"Found {invalid_years} papers with invalid years")
            validation_stats['papers_with_warnings'] += invalid_years
            validation_stats['common_issues'].append('invalid_years')
        else:
            self.logger.validation_result("All publication years valid")

        self.logger.validation_step("Checking journal titles")
        missing_titles = df['journal_title'].isna().sum()
        if missing_titles > 0:
            self.logger.validation_result(f"Found {missing_titles} papers with missing journal titles")
            validation_stats['invalid_papers'] += missing_titles
            validation_stats['common_issues'].append('missing_journal_titles')
        else:
            self.logger.validation_result("All papers have journal titles")

        # Calculate valid papers
        validation_stats['valid_papers'] = (
            validation_stats['total_papers'] 
            - validation_stats['invalid_papers']
        )

        self.logger.validation_summary(validation_stats)

        # Add impact score validation steps
        self.logger.validation_step("Calculating journal impact scores")
        
        # Calculate impact scores first
        # 1. Journal Impact calculation
        scores['journal_impact'] = 0.0
        matched_journals = 0
        total_journals = len(df)
        
        pbar = tqdm(
            df.iterrows(),
            total=len(df),
            desc="Processing Papers",
            unit="",
            ncols=100,
            bar_format="{desc} --> {percentage:3.0f}%|{bar:30}| --> [{n_fmt}/{total_fmt}]",
            miniters=1
        )
        
        for idx, paper in pbar:
            journal_data = self.match_journal(paper['journal_title'], paper.get('issn'))
            if journal_data is not None:
                matched_journals += 1
                sjr_score = journal_data['SJR']
                h_index = journal_data['H index']
                scores.at[idx, 'journal_impact'] = (
                    (sjr_score / self.scimago_df['SJR'].max() * 20) +
                    (h_index / self.scimago_df['H index'].max() * 10)
                )
        
        pbar.close()
        self.logger.validation_result(
            f"Found {matched_journals} out of {total_journals} journals in SCImago database ({(matched_journals/total_journals)*100:.1f}%)"
        )
        
        # 2. Citation Impact
        if 'citation_count' in df.columns:
            scores['citation_impact'] = (
                np.log1p(df['citation_count']) / 
                np.log1p(self.global_max_citations)
            ) * 30
        
        # 3. Recency Impact
        if 'year' in df.columns:
            current_year = datetime.now().year
            years_diff = current_year - df['year']
            scores['recency'] = np.exp(-0.1 * years_diff) * 15  # Exponential decay
        
        # 4. International Collaboration - Fixed calculation
        try:
            df['international_collab'] = df['affiliations'].fillna('').apply(
                lambda x: len(set([
                    aff.split(',')[-1].strip() 
                    for aff in str(x).split(';')
                    if aff.strip()
                ])) > 1
            )
            scores['collaboration'] = df['international_collab'].astype(float) * 10
            
            collab_count = df['international_collab'].sum()
            self.logger.validation_result(f"Found {int(collab_count)} international collaborations ({(collab_count/len(df))*100:.1f}%)")
        except Exception as e:
            self.logger.warning(f"Could not process international collaborations: {str(e)}")
            df['international_collab'] = False
            scores['collaboration'] = 0
        
        # Calculate total and normalized scores
        scores['total_impact_score'] = scores.sum(axis=1)
        max_score = scores['total_impact_score'].max()
        scores['normalized_impact_score'] = (
            scores['total_impact_score'] / max_score * 100 if max_score > 0 else 0
        )
        
        # Now validate the final impact scores
        self.logger.validation_step("Validating final impact scores")
        valid_scores = scores['normalized_impact_score'].notna().sum()
        zero_scores = len(scores[scores['normalized_impact_score'] == 0])
        
        self.logger.validation_result(
            f"Generated scores for {valid_scores} papers ({(valid_scores/len(df))*100:.1f}%)\n" + \
            f"      Papers with zero scores: {zero_scores} ({(zero_scores/len(df))*100:.1f}%)"
        )
        
        # Calculate and display score distribution
        score_distribution = pd.cut(
            scores['normalized_impact_score'],
            bins=[0, 20, 40, 60, 80, 100],
            labels=['Very Low', 'Low', 'Medium', 'High', 'Very High']
        ).value_counts().sort_index()
        
        self.logger.validation_result("Score distribution:")
        for tier, count in score_distribution.items():
            self.logger.validation_result(f"      {tier}: {count} papers ({(count/len(df))*100:.1f}%)")
        
        # Assign impact tiers after validation
        scores['impact_tier'] = pd.cut(
            scores['normalized_impact_score'],
            bins=[0, 20, 40, 60, 80, 100],
            labels=['Very Low', 'Low', 'Medium', 'High', 'Very High']
        )

        # Combine with original data and return
        results = pd.concat([df, scores], axis=1)
        report = self._generate_report(results, scores)
        
        self.logger.success(f"Processed {len(df)} papers")
        return results, report
    
    def _generate_report(self, results: pd.DataFrame, scores: pd.DataFrame) -> Dict[str, Any]:
        """Generate a detailed analysis report"""
        # Get highest and lowest scoring papers with their journals and titles
        scored_papers = results[scores['normalized_impact_score'] > 0]
        if len(scored_papers) > 0:
            highest_paper = scored_papers.nlargest(1, 'normalized_impact_score').iloc[0]
            lowest_paper = scored_papers.nsmallest(1, 'normalized_impact_score').iloc[0]
            
            report = {
                'highest_score': highest_paper['normalized_impact_score'],
                'highest_score_journal': highest_paper['journal_title'],
                'lowest_score': lowest_paper['normalized_impact_score'],
                'lowest_score_journal': lowest_paper['journal_title'],
                'highest_score_paper_title': highest_paper.get('title', 'N/A'),
                'highest_score_paper_doi': highest_paper.get('doi', 'N/A'),
                'lowest_score_paper_title': lowest_paper.get('title', 'N/A'),
                'lowest_score_paper_doi': lowest_paper.get('doi', 'N/A'),
                'total_papers': len(results),
                'avg_impact_score': scores['normalized_impact_score'].mean(),
                'very_high_impact_papers': len(scores[scores['normalized_impact_score'] >= 80]),
                'high_impact_papers': len(scores[(scores['normalized_impact_score'] >= 60) & (scores['normalized_impact_score'] < 80)]),
                'medium_impact_papers': len(scores[(scores['normalized_impact_score'] >= 40) & (scores['normalized_impact_score'] < 60)]),
                'low_impact_papers': len(scores[(scores['normalized_impact_score'] >= 20) & (scores['normalized_impact_score'] < 40)]),
                'very_low_impact_papers': len(scores[scores['normalized_impact_score'] < 20]),
                'international_collab_pct': (results['international_collab'].mean() * 100),
                'journal_distribution': results['journal_title'].value_counts().to_dict(),
                'year_distribution': results['year'].value_counts().to_dict()
            }
        else:
            report = {
                'highest_score': 0.0,
                'highest_score_journal': 'N/A',
                'lowest_score': 0.0,
                'lowest_score_journal': 'N/A',
                'highest_score_paper_title': 'N/A',
                'highest_score_paper_doi': 'N/A',
                'lowest_score_paper_title': 'N/A',
                'lowest_score_paper_doi': 'N/A',
                'total_papers': len(results),
                'avg_impact_score': scores['normalized_impact_score'].mean(),
                'very_high_impact_papers': len(scores[scores['normalized_impact_score'] >= 80]),
                'high_impact_papers': len(scores[(scores['normalized_impact_score'] >= 60) & (scores['normalized_impact_score'] < 80)]),
                'medium_impact_papers': len(scores[(scores['normalized_impact_score'] >= 40) & (scores['normalized_impact_score'] < 60)]),
                'low_impact_papers': len(scores[(scores['normalized_impact_score'] >= 20) & (scores['normalized_impact_score'] < 40)]),
                'very_low_impact_papers': len(scores[scores['normalized_impact_score'] < 20]),
                'international_collab_pct': (results['international_collab'].mean() * 100),
                'journal_distribution': results['journal_title'].value_counts().to_dict(),
                'year_distribution': results['year'].value_counts().to_dict()
            }
        
        # Add citation statistics
        if 'citation_count' in results.columns:
            report['avg_citations'] = results['citation_count'].mean()
        else:
            report['avg_citations'] = 0.0
        
        # Add journal statistics
        journal_stats = {'q1_percent': 0, 'q2_percent': 0, 'q3_percent': 0, 'q4_percent': 0, 'unranked_percent': 0}
        total_journals = len(results['journal_title'].unique())
        
        if total_journals > 0:
            quartile_counts = defaultdict(int)
            for journal_title in results['journal_title'].unique():
                journal_data = self.match_journal(journal_title)
                if journal_data is not None and 'SJR Best Quartile' in journal_data:
                    quartile_counts[journal_data['SJR Best Quartile']] += 1
                else:
                    quartile_counts['unranked'] += 1
            
            # Calculate percentages
            journal_stats = {
                'q1_percent': (quartile_counts.get('Q1', 0) / total_journals) * 100,
                'q2_percent': (quartile_counts.get('Q2', 0) / total_journals) * 100,
                'q3_percent': (quartile_counts.get('Q3', 0) / total_journals) * 100,
                'q4_percent': (quartile_counts.get('Q4', 0) / total_journals) * 100,
                'unranked_percent': (quartile_counts.get('unranked', 0) / total_journals) * 100
            }
        
        report['journal_stats'] = journal_stats
        
        return report

    def generate_visualizations(self, country_reports: Dict[str, Dict], output_dir: str):
        """Generate comparative visualizations"""
        # Use default matplotlib style instead of seaborn
        plt.style.use('default')
        
        # Configure common style elements
        plt.rcParams['figure.figsize'] = (12, 6)
        plt.rcParams['axes.grid'] = True
        plt.rcParams['grid.alpha'] = 0.3
        
        # 1. Impact Score Distribution
        plt.figure()
        data = [(country, report['avg_impact_score']) 
                for country, report in country_reports.items()]
        countries, scores = zip(*sorted(data, key=lambda x: x[1], reverse=True))
        
        bars = plt.bar(countries, scores)
        plt.title('Average Impact Score by Country', pad=20)
        plt.xlabel('Country')
        plt.ylabel('Impact Score')
        plt.xticks(rotation=45, ha='right')
        
        # Add value labels on top of bars
        for bar in bars:
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:.1f}',
                    ha='center', va='bottom')
            
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'impact_scores.png'))
        plt.close()
        
        # 2. Publication Volume
        plt.figure()
        data = [(country, report['total_papers']) 
                for country, report in country_reports.items()]
        countries, papers = zip(*sorted(data, key=lambda x: x[1], reverse=True))
        
        bars = plt.bar(countries, papers)
        plt.title('Publication Volume by Country', pad=20)
        plt.xlabel('Country')
        plt.ylabel('Number of Papers')
        plt.xticks(rotation=45, ha='right')
        
        # Add value labels on top of bars
        for bar in bars:
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2., height,
                    f'{int(height):,}',
                    ha='center', va='bottom')
            
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'publication_volume.png'))
        plt.close()
        
        # 3. International Collaboration
        plt.figure()
        data = [(country, report['international_collab_pct']) 
                for country, report in country_reports.items()]
        countries, collab = zip(*sorted(data, key=lambda x: x[1], reverse=True))
        
        bars = plt.bar(countries, collab)
        plt.title('International Collaboration Percentage by Country', pad=20)
        plt.xlabel('Country')
        plt.ylabel('International Collaboration (%)')
        plt.xticks(rotation=45, ha='right')
        
        # Add value labels on top of bars
        for bar in bars:
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:.1f}%',
                    ha='center', va='bottom')
            
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'international_collab.png'))
        plt.close()

    def find_global_reference_points(self, papers_dir: str):
        """Analyze all paper files to find global reference points"""
        self.logger.header("Finding Global Reference Points")
        
        all_papers = []
        # Add progress tracking for file loading
        paper_files = glob.glob(os.path.join(papers_dir, "*_papers.csv"))
        self.logger.progress(f"Loading papers from {len(paper_files)} countries")
        
        for paper_file in tqdm(paper_files, desc="Loading country files"):
            country = os.path.basename(paper_file).replace('_papers.csv', '')
            try:
                df = pd.read_csv(paper_file, low_memory=False)  # Add low_memory=False to prevent warnings
                df['country'] = country
                all_papers.append(df)
            except Exception as e:
                self.logger.warning(f"Error loading {country}: {str(e)}")
        
        if not all_papers:
            raise ValueError("No paper data could be loaded")
            
        combined_df = pd.concat(all_papers, ignore_index=True)
        self.logger.info(f"Loaded total {len(combined_df):,} papers")
        
        # Find top cited paper
        citations_col = 'Cited by' if 'Cited by' in combined_df.columns else 'citation_count'
        self.global_max_citations = combined_df[citations_col].max()
        top_cited = combined_df.loc[combined_df[citations_col].idxmax()]
        
        self.logger.section("Most Cited Paper")
        self.logger.info(f"Citations: {int(self.global_max_citations):,}")
        self.logger.info(f"Title: {top_cited.get('Title', 'N/A')}")
        self.logger.info(f"Journal: {top_cited.get('Source title', 'N/A')}")
        self.logger.info(f"Year: {int(top_cited.get('Year', 0))}")
        self.logger.info(f"Country: {top_cited['country']}")
        self.logger.info(f"DOI: {top_cited.get('DOI', 'N/A')}")
        
        # Find top ranked journal with progress tracking
        self.logger.section("Analyzing Journal Rankings")
        journal_rankings = {}
        unique_journals = combined_df['Source title'].unique()
        
        for journal_title in tqdm(unique_journals, desc="Analyzing journals"):
            journal_data = self.match_journal(journal_title)
            if journal_data is not None:
                papers = combined_df[combined_df['Source title'] == journal_title]
                journal_rankings[journal_title] = {
                    'rank': journal_data['SJR'],
                    'h_index': journal_data['H index'],
                    'quartile': journal_data.get('SJR Best Quartile', 'N/A'),
                    'numerical_rank': journal_data.get('Rank', 'N/A'),  # Add numerical rank
                    'paper_count': len(papers),
                    'countries': set(papers['country'].unique()),
                    'total_citations': papers[citations_col].sum()
                }
        
        if not journal_rankings:
            self.logger.warning("No journals could be matched with SCImago database")
            return self.global_max_citations, None
            
        # Find top journal
        top_journal = max(journal_rankings.items(), key=lambda x: x[1]['rank'])
        self.global_top_journal = {
            'title': top_journal[0],
            'sjr': top_journal[1]['rank'],
            'h_index': top_journal[1]['h_index'],
            'quartile': top_journal[1]['quartile'],
            'numerical_rank': top_journal[1]['numerical_rank'],  # Add numerical rank
            'paper_count': top_journal[1]['paper_count'],
            'countries': list(top_journal[1]['countries']),
            'total_citations': top_journal[1]['total_citations']
        }
        
        self.logger.section("Highest Ranked Journal")
        self.logger.info(f"Journal: {self.global_top_journal['title']}")
        self.logger.info(f"SJR Score: {self.global_top_journal['sjr']:.3f}")
        self.logger.info(f"Rank: ({self.global_top_journal['numerical_rank']}) | {self.global_top_journal['quartile']}")  # Modified rank display
        self.logger.info(f"H-index: {self.global_top_journal['h_index']}")
        self.logger.info(f"Number of Papers: {self.global_top_journal['paper_count']}")
        self.logger.info(f"Total Citations: {self.global_top_journal['total_citations']:,}")
        self.logger.info(f"Countries: {', '.join(sorted(self.global_top_journal['countries']))}")
        
        # Store for later use in impact calculations
        self.reference_stats = {
            'max_citations': self.global_max_citations,
            'top_journal_sjr': self.global_top_journal['sjr'],
            'top_journal_h_index': self.global_top_journal['h_index']
        }
        
        return self.global_max_citations, self.global_top_journal

def plot_comparative_analysis(results_by_country):
    """Plot comparative analysis with matplotlib instead of seaborn"""
    try:
        import matplotlib.pyplot as plt
        
        # Set style to a basic matplotlib style
        plt.style.use('default')
        
        # Create figure
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 8))
        
        countries = list(results_by_country.keys())
        # Fix: Use correct key name 'avg_impact_score' instead of 'avg_impact'
        impact_scores = [r['avg_impact_score'] for r in results_by_country.values()]
        paper_counts = [r['total_papers'] for r in results_by_country.values()]
        
        # Plot impact scores
        ax1.barh(countries, impact_scores)
        ax1.set_title('Average Impact Score by Country')
        ax1.set_xlabel('Impact Score')
        
        # Plot paper counts
        ax2.barh(countries, paper_counts)
        ax2.set_title('Total Papers by Country')
        ax2.set_xlabel('Number of Papers')
        
        plt.tight_layout()
        plt.savefig('results/comparative_analysis.png')
        plt.close()
        
    except Exception as e:
        print(f"⚠️ Warning: Could not generate comparative plot: {str(e)}")
        # Continue execution even if plotting fails

def main():
    parser = argparse.ArgumentParser(description='Calculate journal impact scores')
    parser.add_argument('--papers_dir', default='data/papers',
                      help='Directory containing paper CSV files')
    parser.add_argument('--scimago', default='data/scimagojr 2023.csv',
                      help='Path to SCImago journal rankings CSV file')
    parser.add_argument('--output', default='results',
                      help='Output directory for results')
    parser.add_argument('--countries', nargs='*',
                      help='Specific countries to process (optional)')
    
    args = parser.parse_args()
    logger = PrettyLogger()
    
    try:
        if not os.path.isdir(args.papers_dir):
            raise NotADirectoryError(f"Papers directory not found: {args.papers_dir}")
            
        if not os.path.exists(args.scimago):
            raise FileNotFoundError(f"SCImago file not found: {args.scimago}")
            
        # Create output directory if it doesn't exist
        os.makedirs(args.output, exist_ok=True)
        
        # Initialize analyzer
        analyzer = JournalImpactAnalyzer(args.scimago, logger)
        
        # Find global reference points before processing individual countries
        max_citations, top_journal = analyzer.find_global_reference_points(args.papers_dir)
        
        country_reports = {}
        
        # Get list of paper files to process
        if args.countries:
            paper_files = [os.path.join(args.papers_dir, f"{country}_papers.csv") 
                         for country in args.countries]
        else:
            paper_files = [os.path.join(args.papers_dir, f) 
                         for f in os.listdir(args.papers_dir) 
                         if f.endswith('_papers.csv')]
        
        logger.header("Journal Impact Score Analysis")
        
        # Process each country's data
        for paper_file in paper_files:
            country_name = os.path.splitext(os.path.basename(paper_file))[0].replace('_papers', '')
            try:
                # Add a subheader for each country
                logger.header(f"Analysis for {country_name.upper()}", sub=True)  # The subheader will now be visible
                
                # Keep only one progress message
                logger.progress(f"Processing papers from {paper_file}")
                
                # Rest of the existing code...
                country_output_dir = os.path.join(args.output, country_name)
                os.makedirs(country_output_dir, exist_ok=True)
                
                # Process papers
                results, report = analyzer.process_papers(paper_file)
                country_reports[country_name] = report
                
                # Save detailed results
                results.to_csv(os.path.join(country_output_dir, 'impact_scores.csv'), index=False)
                
                # Print country-specific statistics
                logger.print_stats(country_name, report)
                # Fix: Use analyzer's journal_ranks instead of self
                logger.print_journal_distribution(report['journal_distribution'], scimago_ranks=analyzer.journal_ranks)
                logger.print_year_distribution(report['year_distribution'])
                
            except Exception as e:
                logger.error(f"Failed to process {country_name}: {str(e)}")
        
        # Generate comparative analysis
        if len(country_reports) > 1:
            logger.header("Comparative Analysis")
            
            # Prepare data for comparison
            comparison_data = []
            for country, report in country_reports.items():
                comparison_data.append({
                    'name': country,
                    'total_papers': report['total_papers'],
                    'avg_impact_score': report['avg_impact_score'],
                    'international_collab_pct': report['international_collab_pct']
                })
            
            # Print comparison
            logger.print_comparison(comparison_data)
            
            # Save comparative analysis
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            comparative_file = os.path.join(args.output, f'comparative_analysis_{timestamp}.csv')
            pd.DataFrame(comparison_data).to_csv(comparative_file, index=False)
            
            # Generate visualizations
            analyzer.generate_visualizations(country_reports, args.output)
            plot_comparative_analysis(country_reports)
        
        logger.success("Analysis completed successfully!")
        logger.info(f"Results saved in: {args.output}")
        
    except Exception as e:
        logger.error(f"Critical error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()