from hn_crawler.parser import parse_discussion_links, parse_top


def test_parse_top_extracts_items():
    html = """
    <html><body>
      <tr class="athing" id="123">
        <td class="title"><span class="titleline"><a href="https://example.com/a">Title A</a></span></td>
      </tr>
      <tr><td class="subtext"><a href="item?id=123">42 comments</a></td></tr>
    </body></html>
    """
    items = parse_top(html)
    assert len(items) == 1
    item = items[0]
    assert item.item_id == 123
    assert item.title == "Title A"
    assert item.url == "https://example.com/a"
    assert "item?id=123" in item.comments_url


def test_parse_discussion_links_filters_internal():
    html = """
    <html><body>
      <span class="commtext">
        <a href="https://example.com/foo">Foo</a>
        <a href="item?id=999">internal</a>
        <a href="user?id=test">user</a>
      </span>
    </body></html>
    """
    links = parse_discussion_links(html)
    assert links == ["https://example.com/foo"]
