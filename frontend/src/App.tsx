import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import './App.css';
import ReferenceInput from './components/ReferenceInput';
import EntriesBrowser from './components/EntriesBrowser';
import FailedExtractions from './components/FailedExtractions';

function App() {
  return (
    <Router>
      <div className="App">
        <header className="App-header">
          <h1>PMID Preprocessor</h1>
          <nav>
            <Link to="/">Process References</Link>
            <Link to="/entries">Browse Entries</Link>
            <Link to="/failed">Failed Extractions</Link>
          </nav>
        </header>
        
        <main>
          <Routes>
            <Route path="/" element={<ReferenceInput />} />
            <Route path="/entries" element={<EntriesBrowser />} />
            <Route path="/failed" element={<FailedExtractions />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
