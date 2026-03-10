from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from models import (
    Bookmark,
    Tag,
    BookmarkCreate,
    BookmarkOut,
    ExportItem,
    get_db,
)
from ai_service import generate_tags, generate_summary

router = APIRouter()

# Helper: serialize Bookmark with tags
def _bookmark_to_out(db: Session, bookmark: Bookmark) -> BookmarkOut:
    tag_names = [t.tag_name for t in bookmark.tags]
    return BookmarkOut(
        id=bookmark.id,
        title=bookmark.title,
        url=bookmark.url,
        tags=tag_names,
        summary=bookmark.summary,
        created_at=bookmark.created_at,
    )

# ------------------------------------------------------------------
# POST /bookmarks – Quick Add (auto fetch title)
# ------------------------------------------------------------------
import httpx

@router.post("/bookmarks", response_model=BookmarkOut, status_code=status.HTTP_201_CREATED)
async def add_bookmark(payload: BookmarkCreate, db: Session = Depends(get_db)):
    # Fetch the page title – simple HEAD + GET fallback for small pages
    async with httpx.AsyncClient(follow_redirects=True, timeout=10.0) as client:
        try:
            resp = await client.get(str(payload.url), timeout=10.0)
            resp.raise_for_status()
        except Exception as exc:
            raise HTTPException(status_code=400, detail="Unable to fetch URL") from exc
        # Very naive title extraction – look for <title> tags
        text = resp.text
        title_match = re.search(r"<title>(.*?)</title>", text, re.IGNORECASE | re.DOTALL)
        title = title_match.group(1).strip() if title_match else payload.url
    # Create Bookmark
    bookmark = Bookmark(url=str(payload.url), title=title)
    db.add(bookmark)
    db.commit()
    db.refresh(bookmark)
    return _bookmark_to_out(db, bookmark)

# ------------------------------------------------------------------
# GET /bookmarks – List & optional keyword search (simple LIKE)
# ------------------------------------------------------------------
from sqlalchemy import select, or_, func

@router.get("/bookmarks", response_model=List[BookmarkOut])
def list_bookmarks(q: str = None, db: Session = Depends(get_db)):
    stmt = select(Bookmark).where(Bookmark.deleted_at.is_(None))
    if q:
        pattern = f"%{q}%"
        stmt = stmt.where(
            or_(
                Bookmark.title.ilike(pattern),
                Bookmark.url.ilike(pattern),
                Bookmark.id.in_(
                    select(Tag.bookmark_id).where(Tag.tag_name.ilike(pattern))
                ),
            )
        )
    bookmarks = db.execute(stmt).scalars().all()
    return [_bookmark_to_out(db, b) for b in bookmarks]

# ------------------------------------------------------------------
# GET /bookmarks/export – JSON export of all bookmarks
# ------------------------------------------------------------------
@router.get("/bookmarks/export", response_model=List[ExportItem])
def export_bookmarks(db: Session = Depends(get_db)):
    stmt = select(Bookmark).where(Bookmark.deleted_at.is_(None))
    bookmarks = db.execute(stmt).scalars().all()
    result = []
    for b in bookmarks:
        tag_names = [t.tag_name for t in b.tags]
        result.append(
            ExportItem(
                id=b.id,
                title=b.title,
                url=b.url,
                tags=tag_names,
                summary=b.summary,
                created_at=b.created_at,
            )
        )
    return result

# ------------------------------------------------------------------
# POST /bookmarks/{id}/ai-tags – Generate AI tags for a bookmark
# ------------------------------------------------------------------
@router.post("/bookmarks/{bookmark_id}/ai-tags", response_model=List[str])
async def ai_tags_endpoint(bookmark_id: str, db: Session = Depends(get_db)):
    bookmark = db.get(Bookmark, bookmark_id)
    if not bookmark or bookmark.deleted_at:
        raise HTTPException(status_code=404, detail="Bookmark not found")
    # Call AI service
    tags = await generate_tags(bookmark.title, bookmark.url)
    # Persist tags (avoid duplicates)
    for tag in tags:
        if not any(t.tag_name == tag for t in bookmark.tags):
            new_tag = Tag(bookmark_id=bookmark.id, tag_name=tag, is_ai_generated=True)
            db.add(new_tag)
    db.commit()
    db.refresh(bookmark)
    return tags

# ------------------------------------------------------------------
# POST /bookmarks/{id}/ai-summarize – Generate AI summary
# ------------------------------------------------------------------
@router.post("/bookmarks/{bookmark_id}/ai-summarize", response_model=dict)
async def ai_summarize_endpoint(bookmark_id: str, db: Session = Depends(get_db)):
    bookmark = db.get(Bookmark, bookmark_id)
    if not bookmark or bookmark.deleted_at:
        raise HTTPException(status_code=404, detail="Bookmark not found")
    summary = await generate_summary(bookmark.title, bookmark.url)
    bookmark.summary = summary.get("summary", "")
    db.commit()
    db.refresh(bookmark)
    return summary
