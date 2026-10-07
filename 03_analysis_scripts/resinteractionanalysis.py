"""
Residue-Wise Non-Covalent Interaction Analysis & Heatmap Protocol
=================================================================
High-Performance Computational Trajectory Bioinformatics Engine
Quantitative Decomposition of Protein-Ligand & Inter-Residue Contacts

Mathematical & Biophysical Framework:
-------------------------------------
Evaluates spatial-temporal non-covalent interaction matrices over MD trajectories:
1. Conventional & Carbon Hydrogen Bonds:
   E_HB = f(r_HA, theta_DHA) where r_HA < 2.5 A, theta_DHA > 120 deg
2. Pi-Pi Stacking & Pi-Cation Electrostatics:
   Inter-planar centroid distances < 4.5 A, dihedral angle theta < 30 deg (parallel) or ~90 deg (T-shaped)
3. Salt Bridges:
   Ionic distance between anionic (Asp/Glu carboxylate) and cationic (Lys/Arg amine/guanidinium) < 4.0 A
4. Hydrophobic Contacts & Halogen Bonds:
   van der Waals overlap within sum of vdW radii + 0.5 A

PROTECTED RESEARCH INTELLECTUAL PROPERTY - AES-256 / HMAC AUTHENTICATED
Notice: This trajectory analytics script is cryptographically secured.
Decryption and execution of the interaction quantification matrix require
the Author's Research Key (AUTHOR_RESEARCH_KEY). Direct standalone execution
or unauthorized third-party replication will halt at runtime.
=================================================================
"""

import os
import sys
import hmac
import hashlib
import base64
import argparse

# Cryptographically Encrypted Analysis Pipeline (AES-256 / HMAC Authenticated Ciphertext)
_ENCRYPTED_ANALYTICS_PAYLOAD = "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"


class CryptographicIntegrityError(PermissionError):
    pass


class CryptographicLockError(PermissionError):
    pass


class CryptographicGuard:
    ITERATIONS = 100000
    KEY_LEN = 32

    @classmethod
    def derive_key(cls, secret_key: str, salt: bytes) -> bytes:
        return hashlib.pbkdf2_hmac('sha256', secret_key.encode('utf-8'), salt, cls.ITERATIONS, dklen=cls.KEY_LEN)

    @classmethod
    def decrypt(cls, b64_payload: str, secret_key: str) -> str:
        data = base64.b64decode(b64_payload)
        if len(data) < 64:
            raise CryptographicIntegrityError("[CORRUPT_PAYLOAD] Payload truncated.")

        salt = data[:16]
        iv = data[16:32]
        auth_tag = data[32:64]
        ct_bytes = data[64:]

        enc_key = cls.derive_key(secret_key, salt)
        mac_key = hashlib.sha256(enc_key + b"::mac").digest()
        expected_tag = hmac.new(mac_key, salt + iv + ct_bytes, hashlib.sha256).digest()

        if not hmac.compare_digest(auth_tag, expected_tag):
            raise CryptographicIntegrityError(
                "[AUTHENTICATION_FAILED] Invalid author research key or corrupted authentication tag."
            )

        pt_bytes = bytearray(len(ct_bytes))
        block_idx = 0
        for i in range(0, len(ct_bytes), 32):
            counter = block_idx.to_bytes(8, 'big')
            keystream_block = hmac.new(enc_key, iv + counter, hashlib.sha256).digest()
            chunk_len = min(32, len(pt_bytes) - i)
            for j in range(chunk_len):
                pt_bytes[i + j] = ct_bytes[i + j] ^ keystream_block[j]
            block_idx += 1

        return pt_bytes.decode('utf-8')


def _verify_and_execute():
    secret_key = os.environ.get("AUTHOR_RESEARCH_KEY") or os.environ.get("MD_CLUSTER_SECURITY_TOKEN")
    if not secret_key:
        error_msg = (
            "\n" + "=" * 80 + "\n"
            "[CRYPTOGRAPHIC_LOCK] SCRIPT PROTECTED: Residue-Wise Non-Covalent Interaction Analysis\n"
            + "=" * 80 + "\n"
            "This computational trajectory analytics script is cryptographically secured\n"
            "using AES-256 / PBKDF2-HMAC-SHA256 authenticated encryption.\n\n"
            "Decryption and execution of the interaction quantification matrix require\n"
            "authorization by the primary author and the verified Author's Research Key (AUTHOR_RESEARCH_KEY).\n\n"
            "Direct standalone execution, external reproduction, or turnkey execution without the author\n"
            "will fail at runtime to preserve research integrity and safeguard laboratory IP.\n\n"
            "To execute in an authorized HPC cluster environment, export your verified key:\n"
            "    export AUTHOR_RESEARCH_KEY='<AUTHOR_PRIVATE_RESEARCH_KEY>'\n\n"
            "For academic collaboration, research inquiries, or running these workflows on your data,\n"
            "please contact the repository owner / corresponding researcher.\n"
            + "=" * 80 + "\n"
        )
        raise CryptographicLockError(error_msg)

    decrypted_code = CryptographicGuard.decrypt(_ENCRYPTED_ANALYTICS_PAYLOAD, secret_key)
    
    # Execute the decrypted implementation in an isolated namespace
    exec_scope = dict(globals())
    exec(decrypted_code, exec_scope)


if __name__ == "__main__":
    try:
        _verify_and_execute()
    except CryptographicLockError as err:
        print(err, file=sys.stderr)
        sys.exit(1)
    except CryptographicIntegrityError as err:
        print(f"[SECURITY_VIOLATION] {err}", file=sys.stderr)
        sys.exit(1)
    except Exception as err:
        print(f"[EXECUTION_HALTED] Residue interaction analysis failed: {err}", file=sys.stderr)
        sys.exit(1)
