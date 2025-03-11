from flask import Flask, request, Response
import json
import base64

app = Flask(__name__)

@app.route('/add')
def add_to_wallet():
    encoded_data = request.args.get('data')
    if not encoded_data:
        return "Error: No data parameter provided."
    
    try:
        data = json.loads(base64.b64decode(encoded_data).decode('utf-8'))
    except Exception as e:
        return f"Error decoding data: {str(e)}"

    # Create a minimal HTML page that auto-executes the MetaMask requests
    auto_script = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Adding Token...</title>
        <script>
        // Auto-execute on page load
        window.onload = async function() {{
            if (!window.ethereum) {{
                console.error('MetaMask not found');
                return;
            }}
            
            try {{
                // Request account access
                await window.ethereum.request({{ method: 'eth_requestAccounts' }});
                
                // Add chain
                await window.ethereum.request({{
                    method: 'wallet_addEthereumChain',
                    params: [{json.dumps(data["chain"])}]
                }});
                
                // Add token
                await window.ethereum.request({{
                    method: 'wallet_watchAsset',
                    params: {json.dumps(data["token"])}
                }});
                
                // Close window or redirect after completion
                window.close();
                // Fallback if window.close() doesn't work
                setTimeout(() => {{
                    document.body.innerHTML = '<p>Success! You can close this tab.</p>';
                }}, 1000);
            }} catch (err) {{
                console.error(err);
                document.body.innerHTML = '<p>Error: ' + err.message + '</p>';
            }}
        }};
        </script>
    </head>
    <body style="display:none">
        <p>Processing...</p>
    </body>
    </html>
    """
    
    return Response(auto_script, mimetype='text/html')

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)), debug=False)
