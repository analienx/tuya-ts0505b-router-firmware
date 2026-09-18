import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / "firmware" / "app" / "hallbulb_light_state.c"
INCLUDE = ROOT / "firmware" / "app"
HARNESS = ROOT / "tests" / "fixtures" / "light_state_harness.c"


class LightStateCoreTests(unittest.TestCase):
    def test_host_harness(self):
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / ("light_state_test.exe" if os.name == "nt" else "light_state_test")
            if os.name == "nt":
                if not self._compile_windows(out):
                    self.skipTest(
                        "No supported host C compiler detected on Windows; "
                        "the CI Linux job executes this harness with cc/gcc/clang"
                    )
            else:
                self._compile_posix(out)
            result = subprocess.run([str(out)], check=True, capture_output=True, text=True)
            self.assertIn("light-state harness PASS", result.stdout)

    def _compile_posix(self, out):
        cc = shutil.which("cc") or shutil.which("gcc") or shutil.which("clang")
        self.assertIsNotNone(cc, "No host C compiler available")
        self._compile_gnu_like(cc, out)

    def _compile_gnu_like(self, cc, out):
        subprocess.run([
            cc, "-std=c11", "-Wall", "-Wextra", "-Werror",
            "-I", str(INCLUDE), str(CORE), str(HARNESS), "-o", str(out),
        ], check=True, capture_output=True, text=True)

    def _compile_windows(self, out):
        for cc in ("clang", "gcc", "cc"):
            resolved = shutil.which(cc)
            if resolved:
                self._compile_gnu_like(resolved, out)
                return True

        cl = shutil.which("cl")
        if cl:
            self._compile_msvc_direct(cl, out)
            return True

        vswhere = Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")) / (
            "Microsoft Visual Studio/Installer/vswhere.exe"
        )
        if not vswhere.exists():
            return False
        result = subprocess.run([
            str(vswhere), "-latest", "-products", "*",
            "-requires", "Microsoft.VisualStudio.Component.VC.Tools.x86.x64",
            "-property", "installationPath",
        ], check=True, capture_output=True, text=True)
        install = result.stdout.strip()
        if not install:
            return False
        vcvars = Path(install) / "VC/Auxiliary/Build/vcvars64.bat"
        if not vcvars.exists():
            return False
        cmd = (
            f'call "{vcvars}" >nul && '
            f'cl /nologo /W4 /WX /I"{INCLUDE}" "{CORE}" "{HARNESS}" '
            f'/Fe:"{out}"'
        )
        subprocess.run(cmd, cwd=out.parent, shell=True, check=True, capture_output=True, text=True)
        return True

    def _compile_msvc_direct(self, cl, out):
        subprocess.run([
            cl, "/nologo", "/W4", "/WX", f'/I{INCLUDE}',
            str(CORE), str(HARNESS), f'/Fe:{out}',
        ], cwd=out.parent, check=True, capture_output=True, text=True)


if __name__ == "__main__":
    unittest.main()
