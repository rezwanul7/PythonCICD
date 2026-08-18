import argparse

import uvicorn


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the PythonCICD API")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", default=8000, type=int)
    parser.add_argument("--reload", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    browser_host = "localhost" if args.host in {"0.0.0.0", "::"} else args.host
    base_url = f"http://{browser_host}:{args.port}"

    print(f"API:      {base_url}/", flush=True)
    if args.host == "0.0.0.0":
        print(f"Loopback: http://127.0.0.1:{args.port}/", flush=True)
    print(f"Docs:     {base_url}/docs", flush=True)
    print(f"Binding:  http://{args.host}:{args.port}", flush=True)

    uvicorn.run(
        "src.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
    )


if __name__ == "__main__":
    main()
