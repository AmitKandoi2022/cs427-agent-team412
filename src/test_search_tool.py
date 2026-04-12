from minisweagent.tools.search_tool import SearchFileContentTool

def test_search():
    tool = SearchFileContentTool()
    # Update this path to a real file in your repo to test on
    path = "minisweagent/tools/search_tool.py"
    query = "def __call__"

    result = tool({"path": path, "query": query})
    print("Return code:", result["returncode"])
    print("Output:\n", result["output"])

if __name__ == "__main__":
    test_search()