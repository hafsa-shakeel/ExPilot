//src/pages/logout.jsx
import React from 'react';
import { logout } from '../utils/logout';

function Logout() {
  return (
    <button onClick={logout}>
      Logout
    </button>
  );
}

export default Logout;
