import os
import sys
import ctypes

# Reconfigure stdout/stderr to UTF-8 to support printing Unicode Braille characters on Windows
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

# Define path to tables.
# vendor/liblouis-win64 lives two levels above this file (tests/ → root → vendor/).
tables_dir = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "vendor", "liblouis-win64", "share", "liblouis", "tables")
)

# Set Python's environment variable
os.environ["LOUIS_TABLEPATH"] = tables_dir

# On Windows, C DLLs loaded by ctypes often do not see environment variables set via os.environ.
# We explicitly set the environment variable in the C Runtime library (MSVCRT) if on Windows.
if sys.platform == "win32":
    try:
        ctypes.CDLL("msvcrt")._wputenv(f"LOUIS_TABLEPATH={tables_dir}")
        print(f"Propagated LOUIS_TABLEPATH={tables_dir} to C Runtime environment via msvcrt.")
    except Exception as e:
        print(f"Warning: Failed to set LOUIS_TABLEPATH in msvcrt: {e}")

try:
    import louis
except ImportError as e:
    print(f"Failed to import louis: {e}")
    sys.exit(1)

# Try calling lou_setDataPath if exported
try:
    louis.liblouis.lou_setDataPath.argtypes = [ctypes.c_char_p]
    louis.liblouis.lou_setDataPath.restype = None
    louis.liblouis.lou_setDataPath(tables_dir.encode('utf-8'))
    print("Called lou_setDataPath successfully.")
except AttributeError:
    print("lou_setDataPath is not exported by this liblouis version.")
except Exception as e:
    print(f"Error calling lou_setDataPath: {e}")

def run_test():
    # 1. Print liblouis version
    lib_version = louis.version()
    print("=" * 60)
    print(f"Liblouis Version: {lib_version.strip()}")
    print(f"Tables Directory: {tables_dir}")
    print("=" * 60)

    # NOTE: In liblouis, the display table (e.g. unicode.dis) must be specified FIRST
    # in the list of tables to output Unicode Braille characters instead of ASCII Braille.
    table_list_default = ["en-ueb-g2.ctb"]
    table_list_unicode = ["unicode.dis", "en-ueb-g2.ctb"]

    # Verify tables compilation
    try:
        louis.checkTable(table_list_default)
        print("Table 'en-ueb-g2.ctb' compilation: SUCCESS")
    except Exception as e:
        print(f"Table 'en-ueb-g2.ctb' compilation: FAILED - {e}")
        sys.exit(1)

    try:
        louis.checkTable(table_list_unicode)
        print("Table combo 'unicode.dis,en-ueb-g2.ctb' compilation: SUCCESS")
    except Exception as e:
        print(f"Table combo 'unicode.dis,en-ueb-g2.ctb' compilation: FAILED - {e}")

    # Get table info/metadata
    for key in ['about', 'description', 'display-name', 'version']:
        val = louis.getTableInfo("en-ueb-g2.ctb", key)
        if val:
            print(f"Table Info ({key}): {val}")

    # 2. Test translations
    test_sentences = [
        "Hello world!",
        "This is a test of the liblouis Python bindings using UEB Grade 2 literary.",
        "The quick brown fox jumps over the lazy dog."
    ]

    print("\n" + "=" * 60)
    print("TRANSLATION TEST (UEB Grade 2 Literary)")
    print("=" * 60)

    for sentence in test_sentences:
        try:
            translated_ascii = louis.translateString(table_list_default, sentence)
            translated_unicode = louis.translateString(table_list_unicode, sentence)
            print(f"Input            : {sentence}")
            print(f"ASCII Braille    : {translated_ascii}")
            print(f"Unicode Braille  : {translated_unicode}")
            print("-" * 60)
        except Exception as e:
            print(f"Translation failed for '{sentence}': {e}")
            print("-" * 60)

if __name__ == "__main__":
    run_test()
