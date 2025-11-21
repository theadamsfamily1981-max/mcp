"""
Scheduled Scraping System

Automated scraping at optimal times:
- Daily scrapes for all sources
- Hourly checks for watched items
- Custom schedules per source
- Email digests of findings

Uses APScheduler for reliable job scheduling.
"""

import logging
from typing import List, Dict, Callable, Optional
from datetime import datetime, time
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
import asyncio


class ScraperScheduler:
    """
    Schedule automated scraping jobs

    Features:
    - Cron-style scheduling
    - Interval-based scheduling
    - Per-source custom schedules
    - Job history and statistics
    """

    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.job_history: List[Dict] = []
        self.logger = logging.getLogger(self.__class__.__name__)

    def start(self):
        """Start the scheduler"""
        if not self.scheduler.running:
            self.scheduler.start()
            self.logger.info("Scheduler started")

    def shutdown(self):
        """Shutdown the scheduler"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            self.logger.info("Scheduler shutdown")

    def add_daily_job(
        self,
        func: Callable,
        hour: int = 3,
        minute: int = 0,
        job_id: str = None,
        **kwargs
    ):
        """
        Add daily scraping job

        Args:
            func: Async function to call
            hour: Hour to run (0-23)
            minute: Minute to run (0-59)
            job_id: Unique job identifier
            **kwargs: Arguments to pass to func
        """
        trigger = CronTrigger(hour=hour, minute=minute)

        self.scheduler.add_job(
            func,
            trigger=trigger,
            id=job_id,
            kwargs=kwargs,
            replace_existing=True
        )

        self.logger.info(
            f"Added daily job '{job_id}' at {hour:02d}:{minute:02d}"
        )

    def add_hourly_job(
        self,
        func: Callable,
        job_id: str = None,
        **kwargs
    ):
        """
        Add hourly scraping job

        Args:
            func: Async function to call
            job_id: Unique job identifier
            **kwargs: Arguments to pass to func
        """
        trigger = IntervalTrigger(hours=1)

        self.scheduler.add_job(
            func,
            trigger=trigger,
            id=job_id,
            kwargs=kwargs,
            replace_existing=True
        )

        self.logger.info(f"Added hourly job '{job_id}'")

    def add_interval_job(
        self,
        func: Callable,
        minutes: int = None,
        hours: int = None,
        job_id: str = None,
        **kwargs
    ):
        """
        Add interval-based job

        Args:
            func: Async function to call
            minutes: Run every N minutes
            hours: Run every N hours
            job_id: Unique job identifier
            **kwargs: Arguments to pass to func
        """
        trigger = IntervalTrigger(minutes=minutes, hours=hours)

        self.scheduler.add_job(
            func,
            trigger=trigger,
            id=job_id,
            kwargs=kwargs,
            replace_existing=True
        )

        interval_str = f"{hours}h" if hours else f"{minutes}m"
        self.logger.info(f"Added interval job '{job_id}' every {interval_str}")

    def add_cron_job(
        self,
        func: Callable,
        cron_expression: str,
        job_id: str = None,
        **kwargs
    ):
        """
        Add job with cron expression

        Args:
            func: Async function to call
            cron_expression: Cron expression (e.g., "0 */4 * * *" = every 4 hours)
            job_id: Unique job identifier
            **kwargs: Arguments to pass to func
        """
        # Parse cron expression
        parts = cron_expression.split()
        if len(parts) != 5:
            raise ValueError("Cron expression must have 5 parts")

        minute, hour, day, month, day_of_week = parts

        trigger = CronTrigger(
            minute=minute,
            hour=hour,
            day=day,
            month=month,
            day_of_week=day_of_week
        )

        self.scheduler.add_job(
            func,
            trigger=trigger,
            id=job_id,
            kwargs=kwargs,
            replace_existing=True
        )

        self.logger.info(f"Added cron job '{job_id}': {cron_expression}")

    def remove_job(self, job_id: str):
        """Remove scheduled job"""
        self.scheduler.remove_job(job_id)
        self.logger.info(f"Removed job '{job_id}'")

    def list_jobs(self) -> List[Dict]:
        """Get list of scheduled jobs"""
        jobs = []

        for job in self.scheduler.get_jobs():
            jobs.append({
                'id': job.id,
                'name': job.name,
                'next_run': job.next_run_time,
                'trigger': str(job.trigger)
            })

        return jobs

    def record_job_result(
        self,
        job_id: str,
        items_found: int,
        duration_seconds: float,
        success: bool = True,
        error: str = None
    ):
        """Record job execution result"""
        self.job_history.append({
            'job_id': job_id,
            'timestamp': datetime.now(),
            'items_found': items_found,
            'duration_seconds': duration_seconds,
            'success': success,
            'error': error
        })

        # Keep only last 1000 records
        if len(self.job_history) > 1000:
            self.job_history = self.job_history[-1000:]

    def get_job_stats(self, job_id: str) -> Dict:
        """Get statistics for a job"""
        job_runs = [r for r in self.job_history if r['job_id'] == job_id]

        if not job_runs:
            return {'error': 'No history for this job'}

        total_runs = len(job_runs)
        successful_runs = len([r for r in job_runs if r['success']])
        total_items = sum(r['items_found'] for r in job_runs)
        avg_items = total_items / total_runs if total_runs > 0 else 0
        avg_duration = sum(r['duration_seconds'] for r in job_runs) / total_runs if total_runs > 0 else 0

        return {
            'total_runs': total_runs,
            'successful_runs': successful_runs,
            'success_rate': (successful_runs / total_runs) * 100 if total_runs > 0 else 0,
            'total_items_found': total_items,
            'avg_items_per_run': round(avg_items, 1),
            'avg_duration_seconds': round(avg_duration, 1)
        }


class EmailDigestManager:
    """
    Send periodic email digests of findings

    Aggregates results and sends summary emails:
    - Daily digest: New items, price drops, rare finds
    - Weekly digest: Market trends, best deals
    """

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    async def send_daily_digest(
        self,
        new_items: List[Dict],
        price_drops: List[Dict],
        rare_finds: List[Dict],
        recipient_email: str
    ):
        """
        Send daily digest email

        Args:
            new_items: New items found today
            price_drops: Items with price drops
            rare_finds: Rare items found
            recipient_email: Email address
        """
        subject = f"Daily PC Parts Digest - {datetime.now().strftime('%Y-%m-%d')}"

        body = self._build_daily_digest_html(new_items, price_drops, rare_finds)

        # Send email (integrate with existing email system)
        self.logger.info(f"Would send daily digest to {recipient_email}")
        self.logger.debug(f"Digest stats: {len(new_items)} new, {len(price_drops)} drops, {len(rare_finds)} rare")

    def _build_daily_digest_html(
        self,
        new_items: List[Dict],
        price_drops: List[Dict],
        rare_finds: List[Dict]
    ) -> str:
        """Build HTML digest email"""

        html = "<html><body>"
        html += "<h1>📊 Daily PC Parts Digest</h1>"

        # Price Drops
        if price_drops:
            html += "<h2>💰 Price Drops</h2><ul>"
            for item in price_drops[:10]:  # Top 10
                html += f"<li><b>{item['title']}</b> - ${item['price']:.2f} (↓{item['drop_percent']:.0f}%)</li>"
            html += "</ul>"

        # Rare Finds
        if rare_finds:
            html += "<h2>⭐ Rare Finds</h2><ul>"
            for item in rare_finds[:10]:
                html += f"<li><b>{item['title']}</b> - Rarity: {item['rarity_score']}/100</li>"
            html += "</ul>"

        # New Items
        html += f"<h2>📦 New Items ({len(new_items)} total)</h2>"
        html += f"<p>Found {len(new_items)} new items across all sources today.</p>"

        html += "</body></html>"

        return html
