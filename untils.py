import socket

def get_host_ip():
    """
    獲取電腦在 Wi-Fi 中的 IP
    """
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    except Exception:
        # 暫時作法:離線或連線失敗時 fallback 到 localhost，避免例外崩潰
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip