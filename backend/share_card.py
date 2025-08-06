"""
Share card generator for Word Guess Contest game.
"""

import os
import logging
from datetime import timedelta, datetime
from PIL import Image, ImageDraw, ImageFont, ImageColor, ImageFilter
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from typing import Dict, Optional, Tuple, List
from .share_utils import ShareUtils
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ShareCardGenerator:
    def __init__(self):
        # Define paths
        self.assets_dir = 'assets'
        self.font_path = os.path.join(self.assets_dir, 'Roboto-Regular.ttf')
        self.font_bold_path = os.path.join(self.assets_dir, 'Roboto-Bold.ttf')
        
        # Colors
        self.colors = {
            'background': (245, 247, 250),  # Light blue-gray
            'text': (33, 33, 33),          # Dark gray
            'accent': (0, 121, 107),       # Teal
            'gradient_start': (235, 245, 250),  # Light blue
            'gradient_end': (245, 250, 255),    # Very light blue
            'score': {
                'good': (76, 175, 80),     # Green
                'medium': (255, 152, 0),    # Orange
                'bad': (244, 67, 54)       # Red
            },
            'border': (200, 200, 200),      # Light gray
            'qr_background': (255, 255, 255),  # White
            'stats_bg': (255, 255, 255, 180),   # Semi-transparent white
            'graph': {
                'primary': (0, 121, 107),    # Teal
                'secondary': (255, 152, 0),  # Orange
                'tertiary': (244, 67, 54),   # Red
                'quaternary': (76, 175, 80), # Green
                'grid': (200, 200, 200, 50)  # Light gray with transparency
            }
        }
        
        # Dimensions
        self.width = 1200  # Increased width for stats
        self.height = 800  # Increased height for stats
        self.padding = 40
        self.border_radius = 20
        self.qr_size = 100  # Size of QR code on the card
        self.stats_width = 500  # Width of stats section
        self.stats_height = 400  # Height of stats section
        
        # Font sizes
        self.font_sizes = {
            'title': 48,
            'subtitle': 36,
            'text': 24,
            'small': 16,
            'stats': 20,
            'graph_title': 14,
            'graph_label': 12,
            'graph_tick': 10
        }
        
        # Initialize share utils
        self.share_utils = ShareUtils()
        
        # Ensure assets exist
        self._check_assets()
    
    def _check_assets(self):
        """Ensure required assets and directories exist."""
        os.makedirs(self.assets_dir, exist_ok=True)
        os.makedirs('game_data/share_cards', exist_ok=True)
        
        if not all(os.path.exists(f) for f in [self.font_path, self.font_bold_path]):
            logger.warning("Roboto fonts not found. Using default system font.")
    
    def _format_duration(self, seconds: float) -> str:
        """Format duration in seconds to readable time."""
        duration = timedelta(seconds=int(seconds))
        minutes = duration.seconds // 60
        seconds = duration.seconds % 60
        return f"{minutes}m {seconds}s"
    
    def _get_score_color(self, score: int, mode: str) -> tuple:
        """Get appropriate color for score based on mode and value."""
        if mode == "Fun":
            return self.colors['score']['good']
        
        # For Wiz mode, lower is better
        if score <= 10:
            return self.colors['score']['good']
        elif score <= 30:
            return self.colors['score']['medium']
        else:
            return self.colors['score']['bad']
    
    def _create_rounded_rectangle(self, draw: ImageDraw, xy: tuple, radius: int, fill: tuple):
        """Draw a rounded rectangle."""
        x1, y1, x2, y2 = xy
        r = radius
        draw.ellipse((x1, y1, x1 + 2*r, y1 + 2*r), fill=fill)  # Top left
        draw.ellipse((x2 - 2*r, y1, x2, y1 + 2*r), fill=fill)  # Top right
        draw.ellipse((x1, y2 - 2*r, x1 + 2*r, y2), fill=fill)  # Bottom left
        draw.ellipse((x2 - 2*r, y2 - 2*r, x2, y2), fill=fill)  # Bottom right
        draw.rectangle((x1 + r, y1, x2 - r, y2), fill=fill)    # Center
        draw.rectangle((x1, y1 + r, x2, y2 - r), fill=fill)    # Vertical
    
    def _create_gradient_background(self) -> Image.Image:
        """Create a gradient background with rounded corners."""
        image = Image.new('RGB', (self.width, self.height), self.colors['background'])
        draw = ImageDraw.Draw(image)
        
        # Create gradient
        for y in range(self.height):
            r = int(self.colors['gradient_start'][0] + (y / self.height) * 
                   (self.colors['gradient_end'][0] - self.colors['gradient_start'][0]))
            g = int(self.colors['gradient_start'][1] + (y / self.height) * 
                   (self.colors['gradient_end'][1] - self.colors['gradient_start'][1]))
            b = int(self.colors['gradient_start'][2] + (y / self.height) * 
                   (self.colors['gradient_end'][2] - self.colors['gradient_start'][2]))
            draw.line([(0, y), (self.width, y)], fill=(r, g, b))
        
        # Add subtle border
        self._create_rounded_rectangle(
            draw,
            (2, 2, self.width-3, self.height-3),
            self.border_radius,
            self.colors['border']
        )
        
        return image
    
    def _load_fonts(self) -> Dict[str, ImageFont.FreeTypeFont]:
        """Load fonts with fallback to default system font."""
        fonts = {}
        try:
            fonts['title'] = ImageFont.truetype(self.font_bold_path, self.font_sizes['title'])
            fonts['subtitle'] = ImageFont.truetype(self.font_bold_path, self.font_sizes['subtitle'])
            fonts['text'] = ImageFont.truetype(self.font_path, self.font_sizes['text'])
            fonts['small'] = ImageFont.truetype(self.font_path, self.font_sizes['small'])
            fonts['stats'] = ImageFont.truetype(self.font_path, self.font_sizes['stats'])
        except OSError as e:
            logger.warning(f"Failed to load Roboto fonts: {e}. Using default font.")
            fonts['title'] = ImageFont.load_default()
            fonts['subtitle'] = ImageFont.load_default()
            fonts['text'] = ImageFont.load_default()
            fonts['small'] = ImageFont.load_default()
            fonts['stats'] = ImageFont.load_default()
        return fonts

    def _create_stats_visualization(self, player_stats: Dict) -> Optional[Image.Image]:
        """Create a comprehensive statistics visualization image."""
        if not player_stats.get("recent_games"):
            return None

        # Set style
        plt.style.use('seaborn-v0_8')
        sns.set_palette("husl")

        # Create figure with subplots
        fig = plt.figure(figsize=(10, 8), facecolor='none')
        gs = fig.add_gridspec(2, 2, hspace=0.3, wspace=0.3)

        # 1. Score Trend (top left)
        ax1 = fig.add_subplot(gs[0, 0])
        self._plot_score_trend(ax1, player_stats["recent_games"])

        # 2. Question Count Distribution (top right)
        ax2 = fig.add_subplot(gs[0, 1])
        self._plot_question_distribution(ax2, player_stats["recent_games"])

        # 3. Time Distribution (bottom left)
        ax3 = fig.add_subplot(gs[1, 0])
        self._plot_time_distribution(ax3, player_stats["recent_games"])

        # 4. Category Performance (bottom right)
        ax4 = fig.add_subplot(gs[1, 1])
        self._plot_category_performance(ax4, player_stats["recent_games"])

        # Set overall style
        for ax in [ax1, ax2, ax3, ax4]:
            ax.set_facecolor('none')
            ax.grid(True, alpha=0.2, color=self._hex_to_rgb(self.colors['graph']['grid']))
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            for spine in ax.spines.values():
                spine.set_color(self._hex_to_rgb(self.colors['border']))

        # Save to temporary file
        temp_path = "game_data/temp_stats.png"
        plt.savefig(temp_path, transparent=True, bbox_inches='tight', dpi=150)
        plt.close()

        # Load and return the image
        stats_img = Image.open(temp_path)
        os.remove(temp_path)
        return stats_img

    def _plot_score_trend(self, ax: plt.Axes, games: List[Dict]):
        """Plot score trend over the last 12 months (year/month x-axis)."""
        import pandas as pd
        from datetime import datetime
        import numpy as np
        # Prepare DataFrame
        df = pd.DataFrame([
            {"score": g.get("score", 0), "timestamp": g.get("timestamp", None)}
            for g in games if g.get("timestamp")
        ])
        if not df.empty:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df['year_month'] = df['timestamp'].dt.to_period('M').astype(str)
            last_month = pd.Timestamp.now().to_period('M')
            months = [(last_month - i).strftime('%Y-%m') for i in range(11, -1, -1)]
            trend = df.groupby('year_month')['score'].mean().reindex(months, fill_value=np.nan)
            ax.plot(months, trend.values,
                    color=self._hex_to_rgb(self.colors['graph']['primary']),
                    marker='o', linewidth=2, markersize=6)
            # Add trend line if enough points
            valid = ~np.isnan(trend.values)
            if valid.sum() > 1:
                x = np.arange(len(months))[valid]
                y = trend.values[valid]
                z = np.polyfit(x, y, 1)
                p = np.poly1d(z)
                ax.plot(np.array(months)[valid], p(x),
                        color=self._hex_to_rgb(self.colors['graph']['secondary']),
                        linestyle='--', alpha=0.5)
            ax.set_title('Score Trend (Last 12 Months)',
                        fontsize=self.font_sizes['graph_title'],
                        color=self._hex_to_rgb(self.colors['text']))
            ax.set_xlabel('Year/Month',
                        fontsize=self.font_sizes['graph_label'],
                        color=self._hex_to_rgb(self.colors['text']))
            ax.set_ylabel('Average Score',
                        fontsize=self.font_sizes['graph_label'],
                        color=self._hex_to_rgb(self.colors['text']))
            ax.set_xticks(months)
            ax.set_xticklabels(months, rotation=45, ha='right', fontsize=8)
        else:
            ax.set_title('Score Trend (No Data)',
                        fontsize=self.font_sizes['graph_title'],
                        color=self._hex_to_rgb(self.colors['text']))

    def _plot_question_distribution(self, ax: plt.Axes, games: List[Dict]):
        """Plot distribution of questions asked per game."""
        questions = [game.get("questions_count", 0) for game in games]
        
        # Create histogram
        ax.hist(questions, bins=min(len(set(questions)), 10),
                color=self._hex_to_rgb(self.colors['graph']['secondary']),
                alpha=0.7, edgecolor='white')
        
        ax.set_title('Questions per Game', 
                    fontsize=self.font_sizes['graph_title'],
                    color=self._hex_to_rgb(self.colors['text']))
        ax.set_xlabel('Number of Questions', 
                     fontsize=self.font_sizes['graph_label'],
                     color=self._hex_to_rgb(self.colors['text']))
        ax.set_ylabel('Frequency', 
                     fontsize=self.font_sizes['graph_label'],
                     color=self._hex_to_rgb(self.colors['text']))

    def _plot_time_distribution(self, ax: plt.Axes, games: List[Dict]):
        """Plot distribution of time taken per game."""
        times = [game.get("time_taken", 0) / 60 for game in games]  # Convert to minutes
        
        # Create violin plot
        ax.violinplot(times, showmeans=True, showmedians=True)
        
        ax.set_title('Time Distribution', 
                    fontsize=self.font_sizes['graph_title'],
                    color=self._hex_to_rgb(self.colors['text']))
        ax.set_xlabel('Games', 
                     fontsize=self.font_sizes['graph_label'],
                     color=self._hex_to_rgb(self.colors['text']))
        ax.set_ylabel('Time (minutes)', 
                     fontsize=self.font_sizes['graph_label'],
                     color=self._hex_to_rgb(self.colors['text']))

    def _plot_category_performance(self, ax: plt.Axes, games: List[Dict]):
        """Plot average score by category."""
        # Group by category
        categories = {}
        for game in games:
            cat = game.get("subject", "unknown")
            if cat not in categories:
                categories[cat] = {"scores": [], "count": 0}
            categories[cat]["scores"].append(game["score"])
            categories[cat]["count"] += 1
        
        # Calculate averages
        cats = []
        avgs = []
        counts = []
        for cat, data in categories.items():
            cats.append(cat)
            avgs.append(sum(data["scores"]) / len(data["scores"]))
            counts.append(data["count"])
        
        # Create bar plot
        bars = ax.bar(cats, avgs,
                     color=self._hex_to_rgb(self.colors['graph']['quaternary']),
                     alpha=0.7)
        
        # Add count annotations
        for bar, count in zip(bars, counts):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'n={count}',
                   ha='center', va='bottom',
                   fontsize=self.font_sizes['graph_tick'])
        
        ax.set_title('Category Performance', 
                    fontsize=self.font_sizes['graph_title'],
                    color=self._hex_to_rgb(self.colors['text']))
        ax.set_xlabel('Category', 
                     fontsize=self.font_sizes['graph_label'],
                     color=self._hex_to_rgb(self.colors['text']))
        ax.set_ylabel('Average Score', 
                     fontsize=self.font_sizes['graph_label'],
                     color=self._hex_to_rgb(self.colors['text']))
        
        # Rotate category labels for better readability
        plt.setp(ax.get_xticklabels(), rotation=45, ha='right')

    def _hex_to_rgb(self, color: tuple) -> str:
        """Convert RGB tuple to hex color string."""
        return f"#{color[0]:02x}{color[1]:02x}{color[2]:02x}"

    def generate_share_card(
        self,
        word: str,
        category: str,
        score: int,
        duration: float,
        mode: str,
        nickname: Optional[str] = None,
        player_stats: Optional[Dict] = None,
        difficulty: Optional[str] = None,
        output_path: Optional[str] = None,
        is_monthly: bool = False,
        words_solved: Optional[int] = None,  # <-- add this
        **kwargs
    ) -> str:
        """
        Generate a share card image with game results and statistics.
        
        Args:
            word: The word that was guessed
            category: Word category
            score: Final score
            duration: Game duration in seconds
            mode: Game mode (Wiz/Fun)
            nickname: Optional player nickname
            player_stats: Optional player statistics
            difficulty: Optional difficulty
            output_path: Optional custom output path
            is_monthly: Flag indicating if the card is for a monthly high score
            
        Returns:
            Path to the generated image
        """
        try:
            # Prepare output path
            if output_path is None:
                os.makedirs('game_data/share_cards', exist_ok=True)
                safe_nickname = (nickname or 'user').replace(' ', '_').lower()
                output_path = os.path.join('game_data/share_cards', f'share_card_current_{safe_nickname}.png')
            
            # Create gradient background
            image = self._create_gradient_background()
            draw = ImageDraw.Draw(image)
            
            # Load fonts
            fonts = self._load_fonts()
            
            # Draw WizWord title with shadow
            title_y = self.padding
            shadow_offset = 2
            wizword_title = "WizWord"
            date_str = datetime.now().strftime("%Y-%m-%d")
            user_str = f"Player: {nickname}" if nickname else ""
            # Title shadow
            draw.text(
                (self.width//2 + shadow_offset, title_y + shadow_offset),
                wizword_title,
                font=fonts['title'],
                fill=(0, 0, 0, 100),  # Semi-transparent black
                anchor="mm"
            )
            # Title main
            draw.text(
                (self.width//2, title_y),
                wizword_title,
                font=fonts['title'],
                fill=self.colors['text'],
                anchor="mm"
            )
            # Date and user (subtitle)
            subtitle_y = title_y + self.font_sizes['title'] + 10
            subtitle_text = date_str if not user_str else f"{date_str}   |   {user_str}"
            draw.text(
                (self.width//2, subtitle_y),
                subtitle_text,
                font=fonts['subtitle'],
                fill=self.colors['text'],
                anchor="mm"
            )
            
            # Draw word and category
            word_y = subtitle_y + 40
            if is_monthly:
                draw.text(
                    (self.width//2, word_y),
                    "Your Highest Score for this Month",
                    font=fonts['subtitle'],
                    fill=self.colors['text'],
                    anchor="mm"
                )
            elif mode == "Beat":
                # Use words_solved argument if present, else fallback
                ws = words_solved
                if ws is None:
                    ws = kwargs.get('words_solved')
                if ws is None and player_stats and 'words_solved' in player_stats:
                    ws = player_stats['words_solved']
                if ws is None:
                    ws = 0
                draw.text(
                    (self.width//2, word_y),
                    f"Words Solved: {ws}",
                    font=fonts['subtitle'],
                    fill=self.colors['text'],
                    anchor="mm"
                )
            else:
                draw.text(
                    (self.width//2, word_y),
                    f"Word: {word.upper()}",
                    font=fonts['subtitle'],
                    fill=self.colors['text'],
                    anchor="mm"
                )
            draw.text(
                (self.width//2, word_y + 50),
                f"Category: {category}",
                font=fonts['text'],
                fill=self.colors['text'],
                anchor="mm"
            )
            draw.text(
                (self.width//2, word_y + 100),
                f"Mode: {mode}",
                font=fonts['text'],
                fill=self.colors['text'],
                anchor="mm"
            )
            
            # Draw score and time on separate lines to avoid overlap
            score_y = word_y + 180
            score_color = self._get_score_color(score, mode)
            # Use provided difficulty, or fallback to player_stats or N/A
            difficulty_label = difficulty or (player_stats.get('difficulty') if player_stats and 'difficulty' in player_stats else 'N/A')
            draw.text(
                (self.width//2, score_y),
                f"Total Average per Word (Score): {score}",
                font=fonts['subtitle'],
                fill=score_color,
                anchor="mm"
            )
            draw.text(
                (self.width//2, score_y + 50),
                f"Total Average per Word (Seconds): {duration}",
                font=fonts['subtitle'],
                fill=self.colors['text'],
                anchor="mm"
            )
            
            # Draw player stats if available
            if player_stats:
                stats_y = score_y + 80
                
                # Create stats background
                self._create_rounded_rectangle(
                    draw,
                    (self.padding, stats_y, self.width - self.padding, stats_y + self.stats_height),
                    10,
                    self.colors['stats_bg']
                )
                
                # Draw stats text
                stats_text_y = stats_y + 20
                draw.text(
                    (self.width//4, stats_text_y),
                    f"Total Games: {player_stats['total_games']}",
                    font=fonts['stats'],
                    fill=self.colors['text'],
                    anchor="mm"
                )
                draw.text(
                    (2*self.width//4, stats_text_y),
                    f"Best Score: {int(player_stats['best_score'])}",
                    font=fonts['stats'],
                    fill=self.colors['text'],
                    anchor="mm"
                )
                draw.text(
                    (3*self.width//4, stats_text_y),
                    f"Avg Score: {round(player_stats['avg_score'], 1)}",
                    font=fonts['stats'],
                    fill=self.colors['text'],
                    anchor="mm"
                )
                
                # Add stats visualization
                stats_img = self._create_stats_visualization(player_stats)
                if stats_img:
                    # Resize and paste stats visualization
                    stats_img = stats_img.resize(
                        (self.width - 2*self.padding - 40, self.stats_height - 60),
                        Image.Resampling.LANCZOS
                    )
                    image.paste(
                        stats_img,
                        (self.padding + 20, stats_text_y + 30),
                        mask=stats_img if stats_img.mode == 'RGBA' else None
                    )
            
            # Add QR code
            qr_code = self.share_utils.generate_qr_code(word, category, score, duration, mode)
            if qr_code:
                qr_y = self.height - self.qr_size - self.padding
                qr_code = qr_code.resize((self.qr_size, self.qr_size))
                image.paste(qr_code, (self.width - self.qr_size - self.padding, qr_y))
            
            # --- WizWord Official Stamp ---
            # Stamp properties
            stamp_radius = 80
            stamp_center = (self.padding + stamp_radius, self.height - self.padding - stamp_radius)
            stamp_color = self.colors['accent']
            stamp_outline = (33, 33, 33)
            stamp_text = f"Official\nWizWord\n{datetime.now().year}"
            # Draw circle
            draw.ellipse([
                stamp_center[0] - stamp_radius, stamp_center[1] - stamp_radius,
                stamp_center[0] + stamp_radius, stamp_center[1] + stamp_radius
            ], fill=stamp_color, outline=stamp_outline, width=4)
            # Draw text (centered, multiline)
            try:
                stamp_font = fonts.get('subtitle', fonts['title'])
            except Exception:
                stamp_font = fonts['title']
            draw.multiline_text(
                stamp_center,
                stamp_text,
                font=stamp_font,
                fill=(255,255,255),
                anchor="mm",
                align="center",
                spacing=4
            )
            
            # Save the image
            image.save(output_path, "PNG")
            logger.info(f"Share card saved to {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Failed to generate share card: {e}")
            return ""

def create_share_card(game_summary: Dict, is_monthly: bool = False) -> str:
    """
    Create a share card from a game summary.
    
    Args:
        game_summary: Dictionary containing game results
        is_monthly: Flag indicating if the card is for a monthly high score
        
    Returns:
        Path to the generated share card image
    """
    generator = ShareCardGenerator()
    return generator.generate_share_card(
        word=game_summary["word"],
        category=game_summary["subject"],
        score=game_summary["score"],
        duration=game_summary["time_taken"],
        mode=game_summary["mode"],
        nickname=game_summary.get("nickname"),
        player_stats=game_summary.get("player_stats"),
        difficulty=game_summary.get("difficulty"),
        output_path=game_summary.get("output_path"),
        is_monthly=is_monthly,
        words_solved=game_summary.get("words_solved"),  # <-- pass it here
    ) 

def create_monthly_high_score_share_card(stats_manager) -> str:
    """Generate a share card for the highest score achieved by the user in the current month, but only regenerate if older than 1 hour."""
    high_score_game = stats_manager.get_highest_score_game_this_month()
    if not high_score_game:
        logger.info("No games played this month. No share card generated.")
        return ""
    # Determine output path
    word = high_score_game["word"].lower()
    nickname = high_score_game.get("nickname", "user")
    output_path = os.path.join('game_data/share_cards', f'share_card_{nickname}_{word}_monthly.png')
    # Fix duration for Beat mode
    mode = high_score_game.get("mode", "")
    if mode == "Beat":
        beat_mode_time = int(os.getenv("BEAT_MODE_TIME", 300))
        high_score_game["duration"] = beat_mode_time
        high_score_game["time_taken"] = beat_mode_time
    # Check if file exists and is less than 1 hour old
    if os.path.exists(output_path):
        mtime = os.path.getmtime(output_path)
        if time.time() - mtime < 3600:
            logger.info(f"Returning cached share card: {output_path}")
            return output_path
    # Regenerate share card
    return create_share_card({**high_score_game, "output_path": output_path}, is_monthly=True) 