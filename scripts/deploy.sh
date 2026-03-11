#!/bin/bash
# Deploy Signal Hunters website to Hostinger
# Usage: ./scripts/deploy.sh

export SSH_ASKPASS_REQUIRE=force
export SSH_ASKPASS=/tmp/ssh_pass_hostinger.sh

# Create password helper
cat > /tmp/ssh_pass_hostinger.sh << 'PASS'
#!/bin/bash
echo "Phat2511@"
PASS
chmod +x /tmp/ssh_pass_hostinger.sh

cd /home/shinyyume/.openclaw/workspace/signal-hunters-web

rsync -avz --progress --exclude='.git' --exclude='scripts' --exclude='docs' \
  -e "ssh -o StrictHostKeyChecking=no -p 65002" \
  ./ u219040996@153.92.8.178:domains/daututhongminh24h.com/public_html/

echo "✅ Deploy complete!"
