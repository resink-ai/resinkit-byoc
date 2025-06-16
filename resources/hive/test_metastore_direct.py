#!/usr/bin/env python3
"""
Test Hive Metastore using PyHive
Install: pip install pyhive thrift-sasl
Run: HOST_HIVE_SERVER2=hiveserver2 HOST_METASTORE=hive-metastore uv run python3 test_metastore_direct.py
"""

import socket
from contextlib import contextmanager

import os

HOST_METASTORE = os.getenv("HOST_METASTORE", "localhost")
HOST_HIVE_SERVER2 = os.getenv("HOST_HIVE_SERVER2", "localhost")


def test_basic_connection():
    """Test basic socket connection to metastore"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((HOST_METASTORE, 9083))
        sock.close()

        if result == 0:
            print(f"✅ Metastore port 9083 is accessible on {HOST_METASTORE}")
            return True
        else:
            print(f"❌ Cannot connect to metastore port 9083 on {HOST_METASTORE}")
            return False
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        return False


def test_with_pyhive():
    """Test using PyHive (requires HiveServer2)"""
    try:
        from pyhive import hive

        # Connect to HiveServer2 (not directly to metastore)
        conn = hive.Connection(
            host=HOST_HIVE_SERVER2,
            port=10000,  # HiveServer2 port
            username="root",
        )

        cursor = conn.cursor()

        # Test basic operations
        cursor.execute("SHOW DATABASES")
        databases = cursor.fetchall()
        print(f"✅ Retrieved databases via PyHive: {databases}")

        cursor.close()
        conn.close()
        return True

    except ImportError:
        print("⚠️ PyHive not available. Install with: pip install pyhive")
        return False
    except Exception as e:
        print(f"❌ PyHive test failed: {e}")
        return False


def test_with_manual_thrift():
    """Test basic Thrift connectivity without Hive-specific client"""
    try:
        from thrift.transport import TSocket, TTransport
        from thrift.protocol import TBinaryProtocol

        transport = TSocket.TSocket(HOST_METASTORE, 9083)
        transport = TTransport.TBufferedTransport(transport)
        protocol = TBinaryProtocol.TBinaryProtocol(transport)

        transport.open()
        print("✅ Basic Thrift connection successful")
        transport.close()
        return True

    except ImportError:
        print(
            "⚠ Basic Thrift libraries not available. Install with: pip install thrift"
        )
        return False
    except Exception as e:
        print(f"❌ Basic Thrift test failed: {e}")
        return False


@contextmanager
def suppress_output():
    """Suppress stdout/stderr for cleaner output"""
    import sys
    import os

    with open(os.devnull, "w") as devnull:
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        try:
            sys.stdout = devnull
            sys.stderr = devnull
            yield
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr


def main():
    print("Testing Hive Metastore Connectivity...")
    print("=" * 50)

    # Test 1: Basic connectivity
    print("1. Testing basic socket connection...")
    if not test_basic_connection():
        print("   Metastore is not accessible. Check if services are running.")
        return

    # Test 2: PyHive (recommended)
    print("\n2. Testing with PyHive...")
    test_with_pyhive()

    # Test 3: Basic Thrift connectivity
    print("\n3. Testing basic Thrift connectivity...")
    test_with_manual_thrift()

    print("\n" + "=" * 50)
    print("Installation commands:")
    print("  pip install pyhive[hive]")
    print("  pip install hive-metastore-client")
    print("  pip install thrift thrift-sasl")


if __name__ == "__main__":
    main()
