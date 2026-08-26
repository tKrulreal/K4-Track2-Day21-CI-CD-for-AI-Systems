#!/bin/bash
echo "=== 1. Public IP ==="
curl -s --max-time 5 ifconfig.me || echo "FAILED"
echo ""
echo "=== 2. Current user ==="
whoami
echo ""
echo "=== 3. authorized_keys ==="
cat ~/.ssh/authorized_keys
echo ""
echo "=== 4. Pubkey accepted algorithms ==="
sudo sshd -T 2>/dev/null | grep -i pubkey
echo ""
echo "=== 5. Service income-api ==="
systemctl status income-api --no-pager 2>&1 | head -5
echo ""
echo "=== 6. SELinux ==="
getenforce 2>&1 || echo "N/A"
