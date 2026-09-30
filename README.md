# Company Research Agent

채용공고를 기반으로 기업과 직무에 필요한 정보를 자동으로 조사하고,
출처 기반 Research Report를 생성하는 AI Research Agent 프로젝트입니다.

## Tech Stack

### Frontend
- React
- TypeScript
- Vite

### Backend
- Python
- FastAPI

## Development

### Frontend

```bash
cd frontend
npm run dev
```

### Backend

```bash
uvicorn backend.app.main:app --reload
```

### GitHub 업로드

변경된 파일 확인:
```bash
git status
```
변경사항 스테이징:
```bash
git add .
```
커밋 생성:
```bash
git commit -m "update README"
```
GitHub에 업로드:
```bash
git push
```