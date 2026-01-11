#!/bin/bash
# setup_schedulers.sh - install systemd services and timers for TheBeakers

set -e

CONFIG_DIR="/storage/thebeakers/config"
LOG_DIR="/storage/thebeakers/logs"

echo "=== TheBeakers Scheduler Setup ==="

# create logs directory
mkdir -p "$LOG_DIR"
echo "created logs directory: $LOG_DIR"

# copy service and timer files
echo "copying service files..."
sudo cp "$CONFIG_DIR/thebeakers-daily.service" /etc/systemd/system/
sudo cp "$CONFIG_DIR/thebeakers-daily.timer" /etc/systemd/system/
sudo cp "$CONFIG_DIR/thebeakers-weekly.service" /etc/systemd/system/
sudo cp "$CONFIG_DIR/thebeakers-weekly.timer" /etc/systemd/system/

# ensure subscribe API service is also installed
if [ -f "$CONFIG_DIR/thebeakers-subscribe.service" ]; then
    sudo cp "$CONFIG_DIR/thebeakers-subscribe.service" /etc/systemd/system/
fi

# reload systemd
echo "reloading systemd..."
sudo systemctl daemon-reload

# enable and start timers
echo "enabling timers..."
sudo systemctl enable thebeakers-daily.timer
sudo systemctl enable thebeakers-weekly.timer

sudo systemctl start thebeakers-daily.timer
sudo systemctl start thebeakers-weekly.timer

# enable subscribe API (runs continuously)
if [ -f /etc/systemd/system/thebeakers-subscribe.service ]; then
    echo "enabling subscribe API service..."
    sudo systemctl enable thebeakers-subscribe.service
    sudo systemctl start thebeakers-subscribe.service
fi

echo ""
echo "=== Status ==="
echo "daily timer:"
systemctl status thebeakers-daily.timer --no-pager || true
echo ""
echo "weekly timer:"
systemctl status thebeakers-weekly.timer --no-pager || true
echo ""
echo "subscribe API:"
systemctl status thebeakers-subscribe.service --no-pager || true

echo ""
echo "=== Next Scheduled Runs ==="
systemctl list-timers thebeakers-* --no-pager

echo ""
echo "=== Setup Complete ==="
echo "to run manually:"
echo "  sudo systemctl start thebeakers-daily.service"
echo "  sudo systemctl start thebeakers-weekly.service"
echo ""
echo "to check logs:"
echo "  journalctl -u thebeakers-daily.service"
echo "  tail -f /storage/thebeakers/logs/daily-digest.log"
