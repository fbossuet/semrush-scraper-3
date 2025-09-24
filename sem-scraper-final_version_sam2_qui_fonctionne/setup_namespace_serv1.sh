#!/bin/bash

set -e

# Charger les variables d'environnement depuis config.env
if [ -f "config.env" ]; then
    echo "[+] Chargement des variables depuis config.env..."
    . config.env
else
    echo "[!] Fichier config.env non trouvé"
    exit 1
fi

# Variables
NAMESPACE1="vpn1"
NAMESPACE2="vpn2"
NAMESPACE3="vpn3"
NAMESPACE4="vpn4"
NAMESPACE5="vpn5"
NAMESPACE6="vpn6"

VETH1="veth-vpn1"
VPEER1="vpeer-vpn1"
VETH2="veth-vpn2"
VPEER2="vpeer-vpn2"
VETH3="veth-vpn3"
VPEER3="vpeer-vpn3"
VETH4="veth-vpn4"
VPEER4="vpeer-vpn4"
VETH5="veth-vpn5"
VPEER5="vpeer-vpn5"
VETH6="veth-vpn6"
VPEER6="vpeer-vpn6"

VPN_CONF1="./NORDVPN/be195.nordvpn.com.tcp.ovpn"
VPN_CONF2="./NORDVPN/be206.nordvpn.com.tcp.ovpn"
VPN_CONF3="./NORDVPN/be213.nordvpn.com.tcp.ovpn"
VPN_CONF4="./NORDVPN/fr800.nordvpn.com.tcp.ovpn"
VPN_CONF5="./NORDVPN/fr806.nordvpn.com.tcp.ovpn"
VPN_CONF6="./NORDVPN/fr1015.nordvpn.com.tcp.ovpn"

# 0. Installation
apt update && apt upgrade -y
apt install python3 python3-pip -y
apt update && apt install -y \
    xvfb x11-utils openvpn screen

# 1. Nettoyage préalable
screen -ls | grep -q "No Sockets" || { screen -X quit; pkill screen; }
pgrep openvpn && sudo killall openvpn

# Nettoyage des namespaces existants
NAMESPACES=("$NAMESPACE1" "$NAMESPACE2" "$NAMESPACE3" "$NAMESPACE4" "$NAMESPACE5" "$NAMESPACE6")
for NS in "${NAMESPACES[@]}"; do
    if sudo ip netns list | grep -q "$NS"; then
        sudo ip netns exec "$NS" killall openvpn || true
        sudo ip netns exec "$NS" vncserver -kill :1 2>/dev/null || true
        sudo ip netns del "$NS" || true
    fi
    pgrep -f "ip netns exec $NS openvpn" && sudo pkill -f "ip netns exec $NS openvpn" || true
done

# Nettoyage des interfaces veth
VETHS=("$VETH1" "$VETH2" "$VETH3" "$VETH4" "$VETH5" "$VETH6")
for VTH in "${VETHS[@]}"; do
    if ip link show "$VTH" &>/dev/null; then
        sudo ip link del "$VTH" || true
    fi
done

# Nettoyage NAT et écrans
if sudo iptables -t nat -L POSTROUTING -n -v | grep -q "MASQUERADE"; then
    sudo iptables -t nat -F POSTROUTING
fi

# Nettoyage des écrans Xvfb
for i in {101.107}; do
    if [ -f "/tmp/.X$i-lock" ]; then
        sudo rm -f "/tmp/.X$i-lock" || true
    fi
done

if pgrep -x "X" > /dev/null; then
    sudo pkill X || true
fi
if pgrep -x "Xvfb" > /dev/null; then
    sudo pkill Xvfb || true
fi

# 2. Lancer Xvfb pour chaque instance
echo "[+] Démarrage des écrans Xvfb..."
for i in {0..5}; do
    display=$((101 + i))
    Xvfb :"$display" -screen 0 1280x720x24 &
    echo "[+] Xvfb lancé sur le display :$display"
done

# 3. Création des namespaces
echo "[+] Création des namespaces..."
for NS in "${NAMESPACES[@]}"; do
    sudo ip netns add "$NS"
    echo "[+] Namespace $NS créé"
done

# 4 & 5. Création des paires veth et attribution aux namespaces
echo "[+] Création et attribution des interfaces veth..."
for i in {1..6}; do
    VETH="VETH$i"
    VPEER="VPEER$i"
    NS="NAMESPACE$i"
    
    sudo ip link add ${!VETH} type veth peer name ${!VPEER}
    sudo ip link set ${!VPEER} netns ${!NS}
    echo "[+] Interface ${!VETH} <-> ${!VPEER} créée et assignée à ${!NS}"
done

# 6. Configuration des interfaces
echo "[+] Configuration des interfaces..."
for i in {1..6}; do
    VETH="VETH$i"
    VPEER="VPEER$i"
    NS="NAMESPACE$i"
    
    sudo ip netns exec ${!NS} ip addr add 10.200.$i.2/24 dev ${!VPEER}
    sudo ip addr add 10.200.$i.1/24 dev ${!VETH}
    
    sudo ip netns exec ${!NS} ip link set ${!VPEER} up
    sudo ip link set ${!VETH} up
    
    echo "[+] Interface ${!VETH} <-> ${!VPEER} configurée"
done

# 7. Activer le loopback dans chaque namespace
echo "[+] Activation des interfaces loopback..."
for NS in "${NAMESPACES[@]}"; do
    sudo ip netns exec "$NS" ip link set lo up
done

# 8. Activer le NAT sur le host
echo "[+] Activation du NAT..."
sudo iptables -t nat -A POSTROUTING -s 10.200.0.0/16 -j MASQUERADE
sudo sysctl -w net.ipv4.ip_forward=1 > /dev/null

# 9. Ajouter la route par défaut dans les namespaces
echo "[+] Configuration des routes par défaut..."
for i in {1..6}; do
    NS="NAMESPACE$i"
    sudo ip netns exec ${!NS} ip route add default via 10.200.$i.1
done

# 10. Ajouter un DNS fonctionnel via /etc/netns
echo "[+] Configuration du DNS (Cloudflare)..."
for NS in "${NAMESPACES[@]}"; do
    sudo mkdir -p /etc/netns/"$NS"
    echo "nameserver 1.1.1.1" | sudo tee /etc/netns/"$NS"/resolv.conf > /dev/null
done

# 11. Lancer OpenVPN dans chaque namespace
echo "[+] Lancement d'OpenVPN dans les namespaces..."

# Vérifier que les variables sont définies
if [ -z "$NORDVPN_USERNAME" ] || [ -z "$NORDVPN_PASSWORD" ]; then
    echo "[!] Erreur: Variables NORDVPN_USERNAME ou NORDVPN_PASSWORD non définies"
    echo "[!] Vérifiez que config.env contient ces variables"
    exit 1
fi

# Créer un répertoire temporaire pour les fichiers d'authentification
sudo mkdir -p ./temp_auth
sudo chmod 700 ./temp_auth
sudo chown $USER:$USER ./temp_auth

for i in {1..6}; do
    NS="NAMESPACE$i"
    CONF="VPN_CONF$i"
    
    # Vérifier que le fichier de configuration existe
    if [ ! -f "${!CONF}" ]; then
        echo "[!] Erreur: Fichier de configuration ${!CONF} non trouvé"
        exit 1
    fi
    
    echo "[+] Démarrage du VPN dans ${!NS} avec ${!CONF}"
    # Créer le fichier d'authentification dans le répertoire temporaire
    sudo bash -c "echo '$NORDVPN_USERNAME' > ./temp_auth/nordvpn_auth_$i"
    sudo bash -c "echo '$NORDVPN_PASSWORD' >> ./temp_auth/nordvpn_auth_$i"
    sudo chmod 600 ./temp_auth/nordvpn_auth_$i
    sudo ip netns exec ${!NS} openvpn --config "${!CONF}" --auth-user-pass ./temp_auth/nordvpn_auth_$i --daemon
done

sleep 10

# 12. Installer les dépendances nécessaires dans chaque namespace
DEPENDENCY_PACKAGES="python3 python3-pip xvfb x11-utils openbox libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 \
    libxcomposite1 libxdamage1 libxrandr2 libgbm1 libasound2 libpangocairo-1.0-0 \
    libxss1 libgtk-3-0 libxshmfence1 libxinerama1 libxcb1 libxext6 libx11-xcb1 \
    fonts-liberation lsb-release xdg-utils openvpn screen"

PYTHON_PACKAGES="pip3 install playwright tqdm && \
    python3 -m playwright install-deps && \
    python3 -m playwright install && \
    python3 -m playwright install chromium && \
    pip3 install bs4 && \
    pip3 install playwright-stealth"

echo "[+] Installation des dépendances dans les namespaces..."
for NS in "${NAMESPACES[@]}"; do
    echo "[+] Installation des dépendances dans $NS..."
    sudo ip netns exec "$NS" bash -c "apt update && apt install -y $DEPENDENCY_PACKAGES"
    echo "[+] Installation des packages Python dans $NS..."
    sudo ip netns exec "$NS" bash -c "pip3 install playwright tqdm playwright-stealth bs4 python-dotenv requests"
    echo "[+] Installation de Playwright dans $NS..."
    sudo ip netns exec "$NS" bash -c "python3 -m playwright install-deps"
    sudo ip netns exec "$NS" bash -c "python3 -m playwright install chromium"
done

# 13. Vérification connectivité & IP publique
echo ""
echo "[+] Vérification des connexions VPN..."
for NS in "${NAMESPACES[@]}"; do
    echo "[*] $NS → IP publique : $(sudo ip netns exec "$NS" curl -s --max-time 5 https://ifconfig.me || echo "DNS KO")"
done