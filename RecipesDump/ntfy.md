# Install

```bash
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://archive.heckel.io/apt/pubkey.txt | sudo gpg --dearmor -o /etc/apt/keyrings/archive.heckel.io.gpg
sudo apt install apt-transport-https
sudo sh -c "echo 'deb [arch=amd64 signed-by=/etc/apt/keyrings/archive.heckel.io.gpg] https://archive.heckel.io/apt debian main' \ > /etc/apt/sources.list.d/archive.heckel.io.list"
sudo apt update && sudo apt install ntfy
vi /etc/ntfy/client.yml # for root
# sudo systemctl enable ntfy
# sudo systemctl start ntfy
```