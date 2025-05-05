import requests
from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning
import re
import warnings
import random

def extract_papers_links(xml_url: str) -> list[str]:
    warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)
    response = requests.get(xml_url)
    soup = BeautifulSoup(response.text, 'lxml')

    loc_tags = soup.find_all('loc')
    pattern = re.compile(r'^https://paperswithcode\.com/sitemap-papers\.xml\?p=\d+$')
    links = [tag.get_text(strip=True) for tag in loc_tags if pattern.match(tag.get_text(strip=True))]
    return links

def extract_author_links(xml_url: str) -> list[str]:
    warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)
    response = requests.get(xml_url)
    soup = BeautifulSoup(response.text, 'lxml')

    loc_tags = soup.find_all('loc')
    links = [tag.get_text(strip=True) for tag in loc_tags]
    return links

def find_repos(url: str) -> list[str] | None:
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    code_section = soup.find('div', id='code')
    if not code_section:
        return None

    implementations_div = code_section.find('div', class_='paper-implementations')
    if not implementations_div:
        return None

    repo_rows = implementations_div.find_all('div', class_='row')
    if not repo_rows:
        return None

    github_links: list[str] = []
    for row in repo_rows:
        link_tag = row.find('a', class_='code-table-link', href=True)
        if link_tag:
            github_links.append(link_tag['href'])

    return list(set(github_links)) if github_links else None

'''def get_all_projects(xml_url: str) -> dict[str, list[str] | None]:
    res: dict[str, list[str] | None] = {}

    papers_links = extract_papers_links(xml_url)
    for paper_link in papers_links:
        author_links = extract_author_links(paper_link)

        for author_link in author_links:
            try:
                repos = find_repos(author_link)
                res.update({author_link: repos})
            except:
                print(f"ERROR: paper_link = {paper_link}, author_link = {author_link}")
                res.update({author_link: None})

    return res'''

def get_all_papers(xml_url: str) -> list[str]:
    res: list[str] = []

    papers_links = extract_papers_links(xml_url)
    for paper_link in papers_links:
        print(paper_link)
        res += extract_author_links(paper_link)

    return res

def write_to_txt(strs: list[str]) -> None:
    with open("all_papers.txt", mode="w") as f:
        for s in strs:
            f.write(s)
            f.write("\n")

def get_sample_in_txt(filename: str = "all_papers.txt") -> None:
    all_papers: list[str] = []
    with open(filename) as f:
        all_papers = f.read().splitlines()

    size = len(all_papers)
    sample = random.sample(all_papers, size // 100)
    with open("papers_sample.txt", mode="w") as f:
        for s in sample:
            f.write(s)
            f.write("\n")

def get_sample_repos_in_txt(filename: str = "papers_sample.txt") -> None:
    papers: list[str] = []
    with open(filename) as f:
        papers = f.read().splitlines()

    res: dict[str, list[str] | None] = {}
    for paper in papers:
        print(paper)
        try:
            repos = find_repos(paper)
            res.update({paper: repos})
        except:
            res.update({paper: None})

    with open("github_repos.txt", mode="w") as f:
        for paper, repos in res.items():
            if repos is None:
                continue

            for repo in repos:
                f.write(repo)
                f.write("\n")

def remove_duplicates():
    repos = []
    with open("github_repos.txt", mode="r") as f:
        repos = f.read().splitlines()
        repos = list(set(repos))

    with open("github_repos.txt", mode="w") as f:
        for r in repos:
            f.write(r)
            f.write("\n")

if __name__ == "__main__":
    xml_url = "https://paperswithcode.com/sitemap.xml"
    all_papers = get_all_papers(xml_url)
    write_to_txt(all_papers)
    get_sample_in_txt()
    get_sample_repos_in_txt()
    remove_duplicates()
