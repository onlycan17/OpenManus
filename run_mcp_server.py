# coding: utf-8
"""
OpenManus MCP 서버 실행 모듈
이 모듈은 MCP 서버를 실행하고 관리하는 역할만 담당합니다.
"""

import argparse
from app.mcp.server import MCPServer
from app.logger import logger


def parse_args() -> argparse.Namespace:
    """명령행 인자를 파싱합니다."""
    parser = argparse.ArgumentParser(description="OpenManus MCP Server")
    parser.add_argument(
        "--transport",
        choices=["stdio"],
        default="stdio",
        help="통신 방식 선택 (기본값: stdio)",
    )
    return parser.parse_args()


def main() -> None:
    """MCP 서버를 실행합니다."""
    try:
        args = parse_args()
        logger.info(f"Starting MCP server with {args.transport} transport")

        server = MCPServer()
        server.run(transport=args.transport)

    except KeyboardInterrupt:
        logger.info("Server shutdown requested")
    except Exception as e:
        logger.error(f"Server error: {str(e)}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
