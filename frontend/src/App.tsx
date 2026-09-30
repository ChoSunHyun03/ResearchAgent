import {useState} from "react";
// api.ts에서 만든 checkHealth 함수를 가져옴
import {checkHealth} from "./api";

// React의 메인 컴포넌트
// 현재 화면에 표시되는 UI를 담당함
function App() {
  const [message, setMessage] = useState("");

  const handleCheckHealth = async () => {
    try{
      const data = await checkHealth();
      setMessage(data.message);
    } catch (error) {
      setMessage("Backend 연결에 실패했습니다.");
    }
  };

  return (
  <main>
    <h1>Company Research Agent</h1>
    
    <p>
      채용공고를 기반으로 기업과 직무에 필요한 정보를 조사하는
      AI Research Agent
    </p>

    <button onClick={handleCheckHealth}>
      Backend 연결 확인
    </button>

    {message && <p>{message}</p>}
  </main>
  );
}

export default App;
