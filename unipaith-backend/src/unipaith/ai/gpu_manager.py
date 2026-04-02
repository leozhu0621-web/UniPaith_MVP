"""
AWS GPU instance lifecycle management for LLM serving.

Handles start/stop/health-check of EC2 GPU instances running vLLM.
- g5.xlarge (always-on): Llama 3.1 8B + nomic-embed-text
- g5.12xlarge (on-demand): Llama 3.1 70B
"""

from __future__ import annotations

import asyncio
import logging
import time

import httpx

from unipaith.config import settings

logger = logging.getLogger("unipaith.gpu_manager")


class GPUInstanceManager:
    """Manage an EC2 GPU instance lifecycle."""

    def __init__(self, instance_id: str, endpoint: str, label: str = "gpu"):
        self.instance_id = instance_id
        self.endpoint = endpoint.rstrip("/")
        self.label = label
        self._last_request_time: float | None = None
        self._ec2_client = None

    @property
    def ec2(self):
        if self._ec2_client is None:
            import boto3

            self._ec2_client = boto3.client("ec2", region_name=settings.aws_region)
        return self._ec2_client

    def get_instance_state(self) -> str:
        """Get current EC2 instance state: pending|running|stopping|stopped|terminated."""
        if not self.instance_id:
            return "not-configured"
        try:
            resp = self.ec2.describe_instances(InstanceIds=[self.instance_id])
            return resp["Reservations"][0]["Instances"][0]["State"]["Name"]
        except Exception as e:
            logger.error("[%s] Failed to get instance state: %s", self.label, e)
            return "unknown"

    async def is_running(self) -> bool:
        state = await asyncio.to_thread(self.get_instance_state)
        return state == "running"

    async def start_instance(self) -> bool:
        """Start the EC2 instance. Returns True if started or already running."""
        if not self.instance_id:
            logger.warning("[%s] No instance_id configured", self.label)
            return False

        state = await asyncio.to_thread(self.get_instance_state)
        if state == "running":
            logger.info("[%s] Instance already running", self.label)
            return True
        if state in ("stopping", "shutting-down", "terminated"):
            logger.warning("[%s] Instance in state '%s', cannot start", self.label, state)
            return False

        logger.info("[%s] Starting instance %s", self.label, self.instance_id)
        try:
            await asyncio.to_thread(self.ec2.start_instances, InstanceIds=[self.instance_id])
            return True
        except Exception as e:
            logger.error("[%s] Failed to start instance: %s", self.label, e)
            return False

    async def stop_instance(self) -> bool:
        """Stop the EC2 instance."""
        if not self.instance_id:
            return False

        state = await asyncio.to_thread(self.get_instance_state)
        if state in ("stopped", "stopping"):
            logger.info("[%s] Instance already stopped/stopping", self.label)
            return True

        logger.info("[%s] Stopping instance %s", self.label, self.instance_id)
        try:
            await asyncio.to_thread(self.ec2.stop_instances, InstanceIds=[self.instance_id])
            return True
        except Exception as e:
            logger.error("[%s] Failed to stop instance: %s", self.label, e)
            return False

    async def wait_until_ready(self, timeout: int | None = None) -> bool:
        """Poll the vLLM health endpoint until it responds 200."""
        timeout = timeout or settings.gpu_70b_cold_start_timeout
        interval = settings.gpu_health_check_interval
        health_url = f"{self.endpoint}/health"

        logger.info("[%s] Waiting for vLLM at %s (timeout=%ds)", self.label, health_url, timeout)
        start = time.monotonic()
        async with httpx.AsyncClient(timeout=10) as client:
            while time.monotonic() - start < timeout:
                try:
                    resp = await client.get(health_url)
                    if resp.status_code == 200:
                        elapsed = time.monotonic() - start
                        logger.info("[%s] vLLM ready after %.1fs", self.label, elapsed)
                        return True
                except (httpx.ConnectError, httpx.TimeoutException):
                    pass
                await asyncio.sleep(interval)

        logger.error("[%s] vLLM not ready after %ds", self.label, timeout)
        return False

    async def ensure_running(self) -> bool:
        """Start instance if stopped, wait until vLLM is ready."""
        started = await self.start_instance()
        if not started:
            return False
        return await self.wait_until_ready()

    def record_request(self) -> None:
        """Record that a request was made (for idle tracking)."""
        self._last_request_time = time.monotonic()

    @property
    def last_request_time(self) -> float | None:
        return self._last_request_time

    @property
    def idle_seconds(self) -> float | None:
        """Seconds since last request, or None if never used."""
        if self._last_request_time is None:
            return None
        return time.monotonic() - self._last_request_time

    async def check_idle_shutdown(self, idle_threshold_minutes: int | None = None) -> bool:
        """Stop instance if idle longer than threshold. Returns True if stopped."""
        threshold = idle_threshold_minutes or settings.gpu_70b_idle_shutdown_minutes
        idle = self.idle_seconds

        if idle is None:
            return False

        if idle > threshold * 60:
            state = await asyncio.to_thread(self.get_instance_state)
            if state == "running":
                logger.info(
                    "[%s] Idle for %.0fs (threshold=%dm), shutting down",
                    self.label,
                    idle,
                    threshold,
                )
                await self.stop_instance()
                return True
        return False


# Singleton managers — lazily initialized
_8b_manager: GPUInstanceManager | None = None
_70b_manager: GPUInstanceManager | None = None


def get_8b_manager() -> GPUInstanceManager:
    global _8b_manager
    if _8b_manager is None:
        _8b_manager = GPUInstanceManager(
            instance_id=settings.gpu_8b_instance_id,
            endpoint=settings.gpu_8b_endpoint,
            label="8B",
        )
    return _8b_manager


def get_70b_manager() -> GPUInstanceManager:
    global _70b_manager
    if _70b_manager is None:
        _70b_manager = GPUInstanceManager(
            instance_id=settings.gpu_70b_instance_id,
            endpoint=settings.gpu_70b_endpoint,
            label="70B",
        )
    return _70b_manager
