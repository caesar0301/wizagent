import re
from typing import Any, Dict, Generator, List, Optional, Tuple, Union

import dotenv
from cogents_core.llm import BaseLLMClient, get_llm_client
from cogents_core.utils import get_logger

dotenv.load_dotenv()

llm_client = get_llm_client()
logger = get_logger(__file__)


def hunyuan_search_with_deep_search(
    client: BaseLLMClient, logger, query: Optional[str] = None, stream: bool = False, debug: bool = False
) -> bool:
    """
    执行Hunyuan深度搜索功能

    :param client: LLM客户端
    :param logger: 日志记录器
    :param query: 用户查询内容，如果为None则使用默认查询
    :param stream: 是否使用流式输出
    :param debug: 调试模式
    :return: 执行结果
    """
    default_query = (
        "通过检索最新的科大讯飞AI相关新闻，从应用落地和营收角度，"
        "分析科大讯飞公司业绩，营收成分。以及行业相关竞争企业的对比分析"
    )

    messages = [
        {"role": "system", "content": "你是一个智能助手，需要根据问题搜索最新信息并给出准确回答。"},
        {
            "role": "user",
            "content": query or default_query,
        },
    ]

    try:
        print("=" * 60)
        print("【正在搜索并生成回答...】")

        response = client.completion(
            messages=messages,
            temperature=0.7,
            max_tokens=2000,
            stream=stream,
            extra_body={
                "enable_enhancement": True,  # 开启增强功能（包含联网搜索）
                "citation": True,  # 开启引文角标（显示信息来源）
                "search_info": True,  # 返回搜索结果信息
                "return_search_results": True,  # 尝试返回搜索结果
                "include_sources": True,  # 尝试包含来源信息
                "return_urls": True,  # 尝试返回URL
                "with_search_details": True,  # 尝试包含搜索详情
            },
        )

        if stream:
            display_streaming_results(response, debug=debug)
        else:
            display_results(response, debug=debug)

        # Enhanced debugging for non-streaming responses to find URLs
        if debug and not stream:
            _inspect_response_for_urls(response, logger)

        # Note: Hunyuan API integrates search results as citations within the content
        # rather than providing them as separate search_info fields
        if debug:
            logger.info("Search results are integrated as citations [1,2,3](@ref) within the response content")

        print(f"\n{'=' * 60}")
        logger.info("✅ completion successful!")
        return True

    except Exception as e:
        logger.error(f"❌ completion failed: {e}")
        return False


def display_streaming_results(response: Generator[Any, None, None], debug: bool = False) -> None:
    """
    处理流式响应，实时显示内容和搜索信息

    :param response: 流式响应生成器
    :param debug: 调试模式
    """
    print("\n" + "=" * 50)
    print("【模型回答】")
    print("=" * 50)

    search_info_collected = None

    content_buffer = ""
    try:
        for chunk in response:
            # Extract content from chunk
            content = _extract_chunk_content(chunk)
            if content:
                content_buffer += content
                print(content, end="", flush=True)

            # Extract search_info from chunk (check multiple locations)
            search_info = _extract_search_info(chunk)
            if search_info:
                search_info_collected = search_info
                if debug:
                    logger.debug(f"Found search_info in streaming chunk: {len(search_info.get('results', []))} results")

        print()  # New line after streaming content

        # Display search information if available
        display_search_info(search_info_collected)

        # Extract and display citation information from the content
        display_citation_summary(content_buffer)

    except Exception as e:
        logger.error(f"Error processing streaming response: {e}")
        print(f"\n处理流式响应时发生错误: {e}")


def display_results(response: Union[str, Dict, Any], debug: bool = False) -> None:
    """
    展示API返回结果，格式化输出内容和来源

    :param response: API响应结果 (可以是字符串、字典或对象)
    :param debug: 调试模式
    """
    try:
        # Extract content and search_info from response
        content = _extract_response_content(response)
        search_info = _extract_search_info(response)

        if not content:
            logger.warning("No valid response content found")
            print("未获取到有效回答")
            return

        print("\n" + "=" * 50)
        print("【模型回答】")
        print(content)
        print("=" * 50)

        # Display search information
        display_search_info(search_info)

        # Extract and display citation information from the content
        display_citation_summary(content)

        if debug and search_info:
            logger.debug(
                f"Response processed successfully with search info: {len(search_info.get('results', []))} sources"
            )

    except Exception as e:
        logger.error(f"Error processing response: {e}")
        print(f"处理响应时发生错误: {e}")


def _extract_chunk_content(chunk: Union[Dict, Any]) -> str:
    """从chunk中提取内容"""
    try:
        if hasattr(chunk, "choices") and chunk.choices:
            choice = chunk.choices[0]
            if hasattr(choice, "delta") and hasattr(choice.delta, "content"):
                return choice.delta.content or ""
        elif isinstance(chunk, dict):
            choices = chunk.get("choices", [])
            if choices:
                delta = choices[0].get("delta", {})
                return delta.get("content", "")
    except (IndexError, AttributeError, KeyError) as e:
        logger.debug(f"Error extracting chunk content: {e}")
    return ""


def _extract_search_info(obj: Union[Dict, Any]) -> Optional[Dict]:
    """从响应对象中提取搜索信息 - 检查多个可能的位置"""
    if not obj:
        return None

    try:
        # Check direct attribute (object format)
        if hasattr(obj, "search_info") and obj.search_info:
            return obj.search_info

        # Check dictionary key (dict format)
        if isinstance(obj, dict):
            # Standard search_info key
            if obj.get("search_info"):
                return obj.get("search_info")

            # Check if obj is the search_info itself
            if "results" in obj:
                return obj

            # Check for alternative locations where search_info might be
            # Some APIs might nest it differently
            for key in ["search_results", "sources", "references", "citations", "citation_sources"]:
                if obj.get(key):
                    return {"results": obj.get(key)}

            # Check for nested structures
            if obj.get("extra") and isinstance(obj.get("extra"), dict):
                extra = obj.get("extra")
                if extra.get("search_info"):
                    return extra.get("search_info")

            # Check for URL-related fields that might contain source information
            if obj.get("urls") or obj.get("source_urls") or obj.get("reference_urls"):
                urls = obj.get("urls") or obj.get("source_urls") or obj.get("reference_urls")
                if isinstance(urls, list):
                    results = []
                    for i, url in enumerate(urls, 1):
                        if isinstance(url, str):
                            results.append({"title": f"引用源 {i}", "url": url, "snippet": ""})
                        elif isinstance(url, dict):
                            results.append(url)
                    return {"results": results}

    except (AttributeError, TypeError) as e:
        logger.debug(f"Error extracting search info: {e}")

    return None


def _extract_response_content(response: Union[str, Dict, Any]) -> str:
    """从响应中提取内容"""
    try:
        if isinstance(response, str):
            return response
        elif isinstance(response, dict):
            choices = response.get("choices", [])
            if choices:
                message = choices[0].get("message", {})
                return message.get("content", "") if isinstance(message, dict) else ""
        else:
            # Handle object response format
            choices = getattr(response, "choices", [])
            if choices:
                try:
                    message = choices[0].message
                    return getattr(message, "content", "")
                except (IndexError, AttributeError):
                    pass
    except (KeyError, TypeError) as e:
        logger.debug(f"Error extracting response content: {e}")
    return ""


def _inspect_response_for_urls(response: Any, logger) -> None:
    """
    深度检查响应对象中是否包含URL信息

    :param response: API响应对象
    :param logger: 日志记录器
    """
    print("\n" + "=" * 50)
    print("【响应结构深度检查】")
    print("=" * 50)

    try:
        # Check if response is a string
        if isinstance(response, str):
            print(f"Response type: string (length: {len(response)})")
            # Look for URLs in the string content
            import re

            url_pattern = r"https?://[^\s\]]+|www\.[^\s\]]+|[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}[^\s\]]*"
            urls = re.findall(url_pattern, response)
            if urls:
                print(f"Found {len(urls)} URLs in content:")
                for i, url in enumerate(urls[:5], 1):  # Show first 5 URLs
                    print(f"  {i}. {url}")
                if len(urls) > 5:
                    print(f"  ... and {len(urls) - 5} more URLs")
            else:
                print("No URLs found in string content")

        # Check if response is a dictionary
        elif isinstance(response, dict):
            print(f"Response type: dict with keys: {list(response.keys())}")
            _recursive_url_search(response, "", 0)

        # Check if response is an object
        else:
            print(f"Response type: {type(response)}")
            if hasattr(response, "__dict__"):
                print(f"Object attributes: {list(response.__dict__.keys())}")
                _recursive_url_search(response.__dict__, "response.__dict__", 0)
            else:
                print("Object has no __dict__ attribute")

    except Exception as e:
        print(f"Error during response inspection: {e}")
        logger.error(f"URL inspection failed: {e}")


def _recursive_url_search(obj: Any, path: str, depth: int, max_depth: int = 3) -> None:
    """
    递归搜索对象中的URL信息

    :param obj: 要搜索的对象
    :param path: 当前路径
    :param depth: 当前深度
    :param max_depth: 最大递归深度
    """
    if depth > max_depth:
        return

    import re

    url_pattern = r"https?://[^\s\]]+|www\.[^\s\]]+|[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}[^\s\]]*"

    try:
        if isinstance(obj, dict):
            for key, value in obj.items():
                current_path = f"{path}.{key}" if path else key

                # Check if key suggests URL content
                if any(url_keyword in key.lower() for url_keyword in ["url", "link", "href", "source", "reference"]):
                    print(f"  Found URL-related key '{current_path}': {value}")

                # Check if value contains URLs
                if isinstance(value, str) and re.search(url_pattern, value):
                    urls = re.findall(url_pattern, value)
                    print(f"  URLs in '{current_path}': {urls}")

                # Recurse into nested structures
                elif isinstance(value, (dict, list)) and depth < max_depth:
                    _recursive_url_search(value, current_path, depth + 1, max_depth)

        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                current_path = f"{path}[{i}]" if path else f"[{i}]"
                _recursive_url_search(item, current_path, depth + 1, max_depth)

        elif isinstance(obj, str) and re.search(url_pattern, obj):
            urls = re.findall(url_pattern, obj)
            print(f"  URLs in '{path}': {urls}")

    except Exception as e:
        print(f"  Error searching path '{path}': {e}")


def extract_citations_from_content(content: str) -> List[Tuple[str, List[int]]]:
    """
    从回答内容中提取引用信息

    :param content: 回答内容
    :return: 引用信息列表，每项为 (文本片段, 引用编号列表) 的元组
    """
    citations = []

    # 匹配引用格式：[1,2,3](@ref) 或 [1](@ref)
    citation_pattern = r"\[([0-9,\s]+)\]\(@ref\)"

    # 找到所有引用
    matches = re.finditer(citation_pattern, content)

    for match in matches:
        citation_numbers_str = match.group(1)
        # 解析引用编号
        numbers = [int(num.strip()) for num in citation_numbers_str.split(",") if num.strip().isdigit()]

        # 获取引用前的文本（用于上下文）
        start_pos = max(0, match.start() - 100)  # 取前100个字符作为上下文
        context = content[start_pos : match.start()].strip()

        # 如果上下文太长，只取最后的句子
        if len(context) > 50:
            sentences = context.split("。")
            context = sentences[-1] if sentences else context[-50:]

        citations.append((context, numbers))

    return citations


def try_extract_urls_from_citations(content: str) -> Dict[int, str]:
    """
    尝试从内容中提取引用对应的URL信息

    :param content: 回答内容
    :return: 引用编号到URL的映射
    """
    url_mapping = {}

    # 尝试匹配可能的URL引用格式
    patterns = [
        r"\[(\d+)\]\(@ref\)\s*(?:https?://[^\s\]]+)",  # [1](@ref) http://...
        r"\[(\d+)\]\(([^)]+)\)",  # [1](url)
        r"\[(\d+)\]:\s*(https?://[^\s]+)",  # [1]: http://...
        r"来源\s*\[(\d+)\]\s*:?\s*(https?://[^\s]+)",  # 来源[1]: http://...
    ]

    for pattern in patterns:
        matches = re.finditer(pattern, content, re.IGNORECASE)
        for match in matches:
            try:
                citation_num = int(match.group(1))
                url = match.group(2) if len(match.groups()) > 1 else None
                if url and url.startswith(("http://", "https://")):
                    url_mapping[citation_num] = url
            except (ValueError, IndexError):
                continue

    return url_mapping


def display_citation_summary(content: str) -> None:
    """
    显示内容中的引用摘要

    :param content: 回答内容
    """
    citations = extract_citations_from_content(content)
    url_mapping = try_extract_urls_from_citations(content)

    if not citations:
        print("\n[信息] 内容中未发现引用标记")
        return

    # 收集所有引用的编号
    all_citations = set()
    for _, numbers in citations:
        all_citations.update(numbers)

    if not all_citations:
        return

    print("\n" + "=" * 50)
    print("【检测到的引用信息】")
    print("=" * 50)

    print(f"共发现 {len(all_citations)} 个引用源：{sorted(all_citations)}")
    print(f"引用片段数量：{len(citations)}")

    # 显示找到的URL（如果有）
    if url_mapping:
        print(f"\n提取到的URL链接：")
        for citation_num, url in sorted(url_mapping.items()):
            print(f"  [{citation_num}] {url}")
    else:
        print("\n未在内容中发现直接的URL链接")

    # 显示引用上下文
    print("\n引用上下文示例：")
    for i, (context, numbers) in enumerate(citations[:3], 1):  # 只显示前3个示例
        urls_for_context = [url_mapping.get(num) for num in numbers if url_mapping.get(num)]
        url_info = f" (URLs: {', '.join(urls_for_context)})" if urls_for_context else ""
        print(f"\n{i}. 「{context}...」→ 引用源 {numbers}{url_info}")

    if len(citations) > 3:
        print(f"\n... 还有 {len(citations) - 3} 个引用片段")

    print("\n[说明] 具体引用源信息由Hunyuan API内部管理，上述编号对应搜索到的相关资料")


def display_search_info(search_info: Optional[Dict]) -> None:
    """
    统一显示搜索信息

    :param search_info: 搜索信息对象或字典
    """
    if not search_info:
        print("\n[信息] 搜索结果已集成在上方回答中的引用标记 [1,2,3](@ref) 中")
        return

    if not isinstance(search_info, dict):
        logger.warning(f"Unexpected search_info format: {type(search_info)}")
        print(f"\n[信息] 搜索信息格式不支持: {type(search_info)}")
        return

    results = search_info.get("results", [])
    if not results:
        print("\n[信息] 搜索结果已集成在上方回答中的引用标记 [1,2,3](@ref) 中")
        return

    print("\n" + "=" * 50)
    print("【信息来源】")
    print("=" * 50)

    try:
        for idx, source in enumerate(results, start=1):
            if isinstance(source, dict):
                title = source.get("title", "无标题")
                url = source.get("url", "未知")
                snippet = source.get("snippet", "无摘要")

                print(f"\n{idx}. {title}")
                print(f"   来源: {url}")
                if snippet and snippet != "无摘要":
                    print(f"   摘要: {snippet}")
            else:
                print(f"\n{idx}. {source}")

        logger.info(f"Displayed {len(results)} search sources")

    except Exception as e:
        logger.error(f"Error displaying search info: {e}")
        print("\n显示搜索结果时出错")


if __name__ == "__main__":
    hunyuan_search_with_deep_search(llm_client, logger, stream=True, debug=False)
