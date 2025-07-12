"""
Constants and configuration for file operations
"""

# File size limits (in bytes)
MAX_FILE_SIZE_READ = 10 * 1024 * 1024  # 10MB
MAX_FILE_SIZE_DISPLAY = 1 * 1024 * 1024  # 1MB for display
MAX_TOTAL_FILES_SCAN = 10000  # Maximum files to scan in operations

# Supported text file extensions
TEXT_FILE_EXTENSIONS = {
    '.txt', '.md', '.py', '.js', '.ts', '.jsx', '.tsx',
    '.html', '.css', '.scss', '.sass', '.less', '.json',
    '.yaml', '.yml', '.toml', '.ini', '.cfg', '.conf',
    '.xml', '.svg', '.csv', '.log', '.sh', '.bash',
    '.zsh', '.fish', '.ps1', '.bat', '.cmd', '.java',
    '.c', '.cpp', '.cc', '.cxx', '.h', '.hpp', '.cs',
    '.go', '.rs', '.rb', '.php', '.pl', '.r', '.sql',
    '.dockerfile', '.gitignore', '.gitattributes',
    '.env', '.example', '.sample', '.template'
}

# Binary file signatures (magic numbers)
BINARY_SIGNATURES = [
    b'\x7fELF',     # ELF executable
    b'\x89PNG',     # PNG image
    b'\xff\xd8',    # JPEG image
    b'GIF8',        # GIF image
    b'PK\x03\x04',  # ZIP archive
    b'\x1f\x8b',    # GZIP archive
    b'BM',          # BMP image
    b'\x00\x00\x01\x00',  # ICO image
]

# Encoding detection order
ENCODING_DETECTION_ORDER = ['utf-8', 'utf-16', 'latin-1', 'ascii']

# Performance limits
MAX_GREP_CONTEXT_LINES = 10
MAX_FIND_RESULTS = 1000
MAX_DIRECTORY_DEPTH = 20