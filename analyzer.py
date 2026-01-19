import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urlparse
import json

class SEOAnalyzer:
    def __init__(self):
        # Use a very common, modern User-Agent to avoid being blocked
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5'
        }

    def analyze_url(self, url, primary_keyword, secondary_keywords):
        """
        Analyzes a single URL for all SEO metrics.
        secondary_keywords: list of strings
        """
        results = {}
        try:
            response = requests.get(url, headers=self.headers, timeout=15)
            results['Status_Code'] = response.status_code
            
            if response.status_code != 200:
                return self._get_error_result(url, response.status_code)

            soup = BeautifulSoup(response.content, 'html.parser')
            
            # --- basic Meta ---
            results['Title'] = soup.title.string.strip() if soup.title else ""
            results['Title_Length'] = len(results['Title'])
            
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            results['Meta_Description'] = meta_desc['content'].strip() if meta_desc and meta_desc.get('content') else ""
            results['Meta_Desc_Length'] = len(results['Meta_Description'])
            
            canonical = soup.find('link', attrs={'rel': 'canonical'})
            results['Canonical_URL'] = canonical['href'] if canonical else ""
            results['Canonical_Type'] = "Self" if results['Canonical_URL'] == url else ("Missing" if not results['Canonical_URL'] else "Canonicalized")
            
            meta_robots = soup.find('meta', attrs={'name': 'robots'})
            results['Meta_Robots'] = meta_robots['content'] if meta_robots else "index, follow" 
            
            # --- Headers ---
            h1_tags = soup.find_all('h1')
            results['H1'] = h1_tags[0].get_text(strip=True) if h1_tags else ""
            results['H1_Count'] = len(h1_tags)
            
            h2_tags = soup.find_all('h2')
            h2_texts = [h.get_text(strip=True) for h in h2_tags]
            
            h3_tags = soup.find_all('h3')
            h3_texts = [h.get_text(strip=True) for h in h3_tags]

            # --- Content ---
            for script in soup(["script", "style"]):
                script.decompose()
            text_content = soup.get_text(separator=' ')
            words = [w for w in text_content.split() if w.strip()]
            results['Word_Count'] = len(words)
            
            first_100_words = " ".join(words[:100]).lower()
            
            # Internal Links
            domain = urlparse(url).netloc
            links = soup.find_all('a', href=True)
            internal_links_count = 0
            for link in links:
                href = link['href']
                if href.startswith('/') or domain in href:
                    internal_links_count += 1
            results['Internal_Links'] = internal_links_count
            
            # Images
            images = soup.find_all('img')
            results['Images'] = len(images)
            missing_alt = []
            for img in images:
                if not img.get('alt'):
                    src = img.get('src', 'unknown_src')
                    missing_alt.append(src.split('/')[-1])
            
            results['Missing_Alt_Count'] = len(missing_alt)
            results['Missing_Alt_Files'] = ", ".join(missing_alt) if missing_alt else "None"

            # --- SCHEMA (Robust) ---
            schemas = []
            
            def extract_types(obj):
                if isinstance(obj, dict):
                    if '@type' in obj:
                        t = obj['@type']
                        if isinstance(t, list): schemas.extend(t)
                        else: schemas.append(t)
                    for k, v in obj.items(): extract_types(v)
                elif isinstance(obj, list):
                    for item in obj: extract_types(item)

            # 1. Parse JSON-LD
            json_ld_scripts = soup.find_all('script', type='application/ld+json')
            for script in json_ld_scripts:
                try:
                    if script.string:
                        data = json.loads(script.string)
                        extract_types(data)
                except: pass
            
            # 2. Parse Microdata
            for item in soup.find_all(attrs={"itemtype": True}):
                try: schemas.append(item['itemtype'].split('/')[-1])
                except: pass
                
            # 3. Fallback: Regex Search for Schema.org types if none found
            if not schemas:
                schema_matches = re.findall(r'"@type":\s*"([^"]+)"', response.text)
                if schema_matches:
                    schemas.extend(schema_matches)

            # --- Layered Schema Classification ---
            
            # Layer 1: Page-Defining Schema (Primary Intent)
            PAGE_DEFINING = {
                'Article', 'BlogPosting', 'NewsArticle', 'TechArticle',
                'Product', 'LocalBusiness', 'Service', 'Restaurant', 
                'FAQPage', 'QAPage', 'Event', 'JobPosting', 'Recipe', 'Review',
                'WebPage', 'MedicalWebPage', 'Course'
            }

            # Layer 2: Entity Schema (Supporting - Report Separately)
            ENTITY_SCHEMAS = {'Person', 'Organization'}

            # Layer 3: Helper / Structural / Ignored (Do not report as primary)
            # WebSite is site-level context, not page intent.
            IGNORED_SCHEMAS = {
                'PostalAddress', 'GeoCoordinates', 'ContactPoint', 'ImageObject', 
                'SearchAction', 'EntryPoint', 'ReadAction', 'AuthorizeAction',
                'Thing', 'Place', 'ListItem', 'BreadcrumbList', 'WebSite',
                'Offer', 'AggregateRating', 'Rating', 'OpeningHoursSpecification',
                'ItemList', 'CollectionPage', 'ProfilePage' 
            }

            primary_schemas = []
            entity_schemas = []

            for s in schemas:
                if not s: continue
                
                if s in PAGE_DEFINING:
                    primary_schemas.append(s)
                elif s in ENTITY_SCHEMAS:
                    entity_schemas.append(s)
                # else: assumes it's either in IGNORED or some unknown helper we don't care about

            # Deduplicate and Sort
            unique_primary = sorted(list(set(primary_schemas)))
            unique_entities = sorted(list(set(entity_schemas)))

            results['Schema_Types'] = ", ".join(unique_primary) if unique_primary else "None"
            results['Schema_Present'] = "Yes" if unique_primary else "No"
            
            # Add Entity info to a new field (optional display support)
            if unique_entities:
                results['Entity_Schema_Present'] = ", ".join(unique_entities)

            # --- KEYWORD ANALYSIS ---
            results['Primary_Keyword'] = primary_keyword
            pk_lower = primary_keyword.lower() if primary_keyword else ""
            
            if pk_lower:
                results['Primary_in_Title'] = "Yes" if pk_lower in results['Title'].lower() else "No"
                results['Primary_in_H1'] = "Yes" if pk_lower in results['H1'].lower() else "No"
                results['Primary_in_URL'] = "Yes" if pk_lower in url.lower() else "No"
                results['Primary_in_Content'] = "Yes" if pk_lower in text_content.lower() else "No"
                results['Primary_in_First_100'] = "Yes" if pk_lower in first_100_words else "No"
                results['Primary_in_Meta_Desc'] = "Yes" if pk_lower in results['Meta_Description'].lower() else "No"
            else:
                # Fill with N/A if no keyword provided
                for k in ['Primary_in_Title', 'Primary_in_H1', 'Primary_in_URL', 'Primary_in_Content', 'Primary_in_First_100', 'Primary_in_Meta_Desc']:
                    results[k] = "N/A"

            # Secondary Analysis
            results['Secondary_Keywords'] = ", ".join(secondary_keywords)
            sec_in_h2 = []
            sec_in_h3 = []
            sec_in_content = []
            
            h2_full_text = " ".join(h2_texts).lower()
            h3_full_text = " ".join(h3_texts).lower()
            content_lower = text_content.lower()
            
            for sk in secondary_keywords:
                sk_lower = sk.strip().lower()
                if not sk_lower: continue
                
                if sk_lower in h2_full_text:
                    sec_in_h2.append(sk)
                if sk_lower in h3_full_text:
                    sec_in_h3.append(sk)
                # Count occurrences in content
                count = content_lower.count(sk_lower)
                if count > 0:
                    sec_in_content.append(f"{sk} ({count})")
            
            results['Secondary_in_H2'] = ", ".join(sec_in_h2) if sec_in_h2 else "None"
            results['Secondary_in_H3'] = ", ".join(sec_in_h3) if sec_in_h3 else "None"
            results['Secondary_in_Content_List'] = ", ".join(sec_in_content) if sec_in_content else "None"

            # --- Issues / Missing Report ---
            issues = []
            
            # 1. Meta / Basic
            if not results['Title']:
                issues.append("Missing Page Title")
            elif len(results['Title']) < 30:
                issues.append(f"Title too short ({len(results['Title'])} chars)")
            elif len(results['Title']) > 60:
                issues.append(f"Title too long ({len(results['Title'])} chars)")
                
            if not results['Meta_Description']:
                issues.append("Missing Meta Description")
            elif len(results['Meta_Description']) < 50:
                 issues.append(f"Meta Description too short ({len(results['Meta_Description'])} chars)")
            elif len(results['Meta_Description']) > 160:
                 issues.append(f"Meta Description too long ({len(results['Meta_Description'])} chars)")
                 
            if not results['Canonical_URL']:
                issues.append("Missing Canonical URL")
            elif results['Canonical_Type'] == "Canonicalized":
                issues.append(f"Page is canonicalized to: {results['Canonical_URL']}")

            # 2. Content
            if not results['H1']:
                issues.append("Missing H1 Tag")
            elif results['H1_Count'] > 1:
                issues.append(f"Multiple H1 Tags found ({results['H1_Count']})")
                
            if results['Word_Count'] < 300:
                issues.append(f"Thin Content (Only {results['Word_Count']} words)")
                
            if results['Missing_Alt_Count'] > 0:
                issues.append(f"Missing Alt Text on {results['Missing_Alt_Count']} images")

            # 3. Schema
            if results['Schema_Present'] == "No":
                issues.append("No Schema Markup detected")

            # 4. Keyword Checks
            if pk_lower:
                if results['Primary_in_Title'] == "No":
                    issues.append("Primary Keyword missing from Title")
                if results['Primary_in_H1'] == "No":
                    issues.append("Primary Keyword missing from H1")
                if results['Primary_in_First_100'] == "No":
                   issues.append("Primary Keyword missing from First 100 Words")
                if results['Primary_in_Meta_Desc'] == "No":
                   issues.append("Primary Keyword missing from Meta Description")

            results['Issues_List'] = issues
            results['Has_Critical_Issues'] = True if issues else False

        except Exception as e:
            return self._get_error_result(url, f"Error: {str(e)}")
            
        return results

    def _get_error_result(self, url, error_msg):
        """Returns a dict structure with empty values but showing the error"""
        keys = ['Title', 'Title_Length', 'Meta_Description', 'Meta_Desc_Length', 'Canonical_URL', 
                'Meta_Robots', 'H1', 'H1_Count', 'Word_Count', 'Internal_Links', 'Images', 
                'Missing_Alt_Count', 'Missing_Alt_Files', 'Schema_Types', 
                'Primary_in_Title', 'Primary_in_H1', 'Primary_in_URL', 'Primary_in_Content', 
                'Primary_in_First_100', 'Primary_in_Meta_Desc', 'Secondary_in_H2', 
                'Secondary_in_H3', 'Secondary_in_Content_List']
        res = {k: "N/A" for k in keys}
        res['Status_Code'] = error_msg
        return res
