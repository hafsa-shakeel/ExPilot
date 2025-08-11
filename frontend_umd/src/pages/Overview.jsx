import React, { useEffect, useState } from 'react';
import API from '../api';
import {
    LineChart, Line, CartesianGrid, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer
} from 'recharts';
import { Modal } from 'react-bootstrap';
import { PieChart, Pie, Cell } from 'recharts';



const Overview = () => {
    const [dashboardData, setDashboardData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [comparisonData, setComparisonData] = useState([]);
    const [compareError, setCompareError] = useState('');
    const [chartData, setChartData] = useState([]);
    const [showChart, setShowChart] = useState(false);
    const [showProfitModal, setShowProfitModal] = useState(false);
    const [selectedBranchId, setSelectedBranchId] = useState(null);
    const [profitSummary, setProfitSummary] = useState(null);
    const [filterYear, setFilterYear] = useState('');
    const [filterMonth, setFilterMonth] = useState('');
    const [showChartModal, setShowChartModal] = useState(false);
    const [chartBranchName, setChartBranchName] = useState('');
    const [data, setData] = useState([]);
    const [pieYear, setPieYear] = useState(new Date().getFullYear());
    const [pieData, setPieData] = useState([]);
    const [pieLoading, setPieLoading] = useState(false);



    useEffect(() => {
        fetchDashboardData();
        fetchComparisonData();
    }, []);

    const fetchDashboardData = async () => {
        try {
            const response = await API.post('/dashboard/summary', {}, { withCredentials: true });
            setDashboardData(response.data);
        } catch (err) {
            setError('Failed to load dashboard data.');
        } finally {
            setLoading(false);
        }
    };

    const fetchComparisonData = async () => {
        try {
            const response = await API.post('/dashboard/branches/compare', {}, { withCredentials: true });
            setComparisonData(response.data.branches_comparison);
        } catch (error) {
            setCompareError("Failed to fetch comparison data.");
        }
    };

    const handleShowChart = async (branchId, branchName) => {
        if (!filterYear) {
            alert("Please select year.");
            return;
        }
        try {
            const res = await API.get(`/dashboard/branches/${branchId}/budget-vs-expense?year=${filterYear}`, {
                withCredentials: true
            });
            setChartData(res.data);
            setChartBranchName(branchName);
            setShowChartModal(true);
        } catch (error) {
            console.error("Chart fetch error:", error);
            setError("Failed to load chart data.");
        }
    };



    const handleViewProfitLoss = async (branchId) => {
        if (!filterYear || !filterMonth) {
            alert("Please select both year and month.");
            return;
        }

        try {
            const monthIndex = [
                "January", "February", "March", "April", "May", "June",
                "July", "August", "September", "October", "November", "December"
            ].indexOf(filterMonth) + 1;

            const res = await API.get(`/dashboard/reports/profit-loss/summary?year=${filterYear}&month=${monthIndex}`, {
                withCredentials: true
            });


            const branchSummary = res.data.summary.find(b => b.branch_id === branchId);
            if (branchSummary) {
                setProfitSummary(branchSummary);
                setSelectedBranchId(branchId);
                setShowProfitModal(true);
            } else {
                alert("No data found for selected branch.");
            }
        } catch (err) {
            console.error("Failed to fetch summary:", err);
        }
    };

    const fetchPieData = async () => {
        setPieLoading(true);
        try {
            const params = pieYear ? { params: { year: pieYear }, withCredentials: true } : { withCredentials: true };
            const res = await API.get('/dashboard/expenses/branch-pie', params);
            setPieData(res.data.filter(d => d.total_expense > 0));
        } catch (err) {
            setPieData([]);
        } finally {
            setPieLoading(false);
        }
    };





    return (
        <div>
            <h3>Dashboard Overview</h3>

            {loading && <p>Loading...</p>}
            {error && <div className="alert alert-danger">{error}</div>}

            {dashboardData && (
                <div className="row text-center">
                    <div className="col-md-3">
                        <div className="card p-3 shadow-sm">
                            <h6>Total Branches</h6>
                            <h4>{dashboardData.total_branches}</h4>
                        </div>
                    </div>
                    <div className="col-md-3">
                        <div className="card p-3 shadow-sm">
                            <h6>Total Branch Budget</h6>
                            <h4>Rs.{dashboardData.monthly_budget}</h4>
                        </div>
                    </div>
                    <div className="col-md-3 position-relative">
                        <div
                            className={`card p-3 shadow-sm ${dashboardData.total_expenses > dashboardData.monthly_budget
                                ? "bg-danger-subtle"
                                : dashboardData.total_expenses < dashboardData.monthly_budget
                                    ? "bg-success-subtle"
                                    : ""
                                }`}
                            style={{
                                backgroundColor:
                                    dashboardData.total_expenses > dashboardData.monthly_budget
                                        ? "#ffe6eb"
                                        : dashboardData.total_expenses < dashboardData.monthly_budget
                                            ? "#e6ffed"
                                            : "",
                            }}
                        >
                            {/* Badge for Loss/Profit */}
                            {dashboardData.total_expenses > dashboardData.monthly_budget && (
                                <span
                                    className="badge bg-danger position-absolute top-0 end-0 translate-middle"
                                    style={{ zIndex: 1, marginTop: "6px", marginRight: "-25px" }}
                                >
                                    Loss
                                </span>
                            )}
                            {dashboardData.total_expenses < dashboardData.monthly_budget && (
                                <span
                                    className="badge bg-success position-absolute top-0 end-0 translate-middle"
                                    style={{ zIndex: 1, marginTop: "6px", marginRight: "-25px" }}
                                >
                                    Profit
                                </span>
                            )}
                            <h6>Total Expenses</h6>
                            <h4>Rs.{dashboardData.total_expenses}</h4>
                        </div>
                    </div>



                    <div className="col-md-3">
                        <div className="card p-3 shadow-sm">
                            <h6>Active Alerts</h6>
                            <h4>{dashboardData.active_alerts}</h4>
                        </div>
                    </div>
                </div>
            )}

            <div className="card p-4 mb-4 mt-4">
                <div className="d-flex align-items-center mb-2">
                    <label className="me-2 fw-bold">Select Year:</label>
                    <select className="form-select w-auto me-3"
                        value={pieYear}
                        onChange={e => setPieYear(Number(e.target.value))}>
                        {[2023, 2024, 2025, 2026, 2027].map(y => (
                            <option key={y} value={y}>{y}</option>
                        ))}
                    </select>
                    <button className="btn btn-sm" style={{ background: '#003153', color: 'white' }}
                        onClick={fetchPieData}>
                        {pieLoading ? "Loading..." : "Load Pie Chart"}
                    </button>
                </div>
                {pieData.length > 0 ? (
                    <ResponsiveContainer width="100%" height={350}>
                        <PieChart>
                            <Pie
                                data={pieData}
                                dataKey="total_expense"
                                nameKey="branch_name"
                                cx="50%"
                                cy="50%"
                                outerRadius={110}
                                label
                            >
                                {pieData.map((entry, idx) => (
                                    <Cell key={entry.branch_id} fill={["#003153", "#005792", "#6ea8fe", "#ffb366", "#ff6384", "#8affb1", "#fdb44b", "#64b5f6"][idx % 8]} />
                                ))}
                            </Pie>
                            <Tooltip />
                            <Legend />
                        </PieChart>
                    </ResponsiveContainer>
                ) : (
                    <div className="text-muted text-center mt-4">
                        {pieLoading ? "Fetching data..." : "No data to display."}
                    </div>
                )}
            </div>

            <div className="row mb-3 mt-4">
                <div className="col-md-3">
                    <select className="form-select" value={filterYear} onChange={(e) => setFilterYear(e.target.value)}>
                        <option value="">Select Year</option>
                        <option>2025</option>
                        <option>2024</option>
                    </select>
                </div>
                <div className="col-md-3">
                    <select className="form-select" value={filterMonth} onChange={(e) => setFilterMonth(e.target.value)}>
                        <option value="">Select Month</option>
                        {["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"].map(month => (
                            <option key={month}>{month}</option>
                        ))}
                    </select>
                </div>
            </div>


            <div className="mt-4s">
                <h5>Compare Branches</h5>
                {compareError && <div className="alert alert-danger">{compareError}</div>}
                {(!comparisonData || comparisonData.length === 0) ? (
                    <p>No comparison data available.</p>
                ) : (
                    <table className="table table-bordered table-striped text-center">
                        <thead className="prussian-header">
                            <tr>
                                <th>Branch Name</th>
                                <th>Total Budget</th>
                                <th>Total Expense</th>
                                <th>Remaining Budget</th>
                                <th>Status</th>
                                <th>Over Budget</th>
                                <th>Alerts</th>
                                <th>Profit/Loss Summary</th>
                            </tr>
                        </thead>
                        <tbody>
                            {comparisonData.map((branch) => (
                                <tr key={branch.branch_id}>
                                    <td>{branch.branch_name}</td>
                                    <td>Rs.{branch.total_budget}</td>
                                    <td>Rs.{branch.total_expense}</td>
                                    <td> {branch.remaining_budget < 0 ? "Rs.0" : `Rs.${branch.remaining_budget}`}</td>
                                    <td>
                                        <span className={`badge bg-${branch.status === 'Profit' ? 'success' : 'danger'}`}>
                                            {branch.status}
                                        </span>
                                    </td>
                                    <td> {branch.over_budget_amount > 0 ? `Rs.-${branch.over_budget_amount}` : "Rs.0"}</td>
                                    <td>{branch.alert_count}</td>
                                    <td><button className="btn btn-sm me-2" style={{ backgroundColor: '#003153', color: 'white' }} onClick={() => handleViewProfitLoss(branch.branch_id)}> View </button></td>
                                    <td>
                                        <div className="d-flex justify-content-center">
                                            <button
                                                className="btn btn-sm"
                                                style={{ backgroundColor: '#003153', color: 'white' }}
                                                onClick={() => handleShowChart(branch.branch_id, branch.branch_name)}
                                            >
                                                Show Chart
                                            </button>
                                        </div>
                                    </td>
                                </tr>
                            ))}

                        </tbody>
                    </table>
                )}

                {showProfitModal && profitSummary && (
                    <Modal show={showProfitModal} onHide={() => setShowProfitModal(false)} centered>
                        <Modal.Header closeButton>
                            <Modal.Title>Profit/Loss Summary</Modal.Title>
                        </Modal.Header>
                        <Modal.Body>
                            <p><strong>Branch:</strong> {profitSummary.branch_name}</p>
                            <p><strong>Year:</strong> {filterYear}</p>
                            <p><strong>Month:</strong> {filterMonth}</p>
                            <p><strong>Budget:</strong> Rs.{profitSummary.budget}</p>
                            <p><strong>Expense:</strong> Rs.{profitSummary.expense}</p>
                            <p><strong>Profit or Loss:</strong> Rs.{profitSummary.profit_or_loss}</p>
                            <p>
                                <strong>Status:</strong>{' '}
                                <span className={`badge ${profitSummary.status === 'Profit' ? 'bg-success' : 'bg-danger'}`}>
                                    {profitSummary.status}
                                </span>
                            </p>
                        </Modal.Body>
                        <Modal.Footer>

                        </Modal.Footer>
                    </Modal>
                )}

                <Modal show={showChartModal} onHide={() => setShowChartModal(false)} size="xl" centered>
                    <Modal.Header closeButton>
                        <Modal.Title>
                            Budget vs Expense Chart – {chartBranchName} ({filterYear})
                        </Modal.Title>
                    </Modal.Header>
                    <Modal.Body>
                        {!chartData || chartData.length === 0 || chartData.every(item => item.total_budget === 0 && item.total_expense === 0) ? (
                            <p className="text-muted">No budget or expense data available for the selected year.</p>
                        ) : (
                            <ResponsiveContainer width="100%" height={300}>
                                <LineChart data={chartData}>
                                    <CartesianGrid stroke="#ccc" />
                                    <XAxis dataKey="month" />
                                    <YAxis />
                                    <Tooltip />
                                    <Legend />
                                    <Line type="monotone" dataKey="total_budget" stroke="#0d6efd" name="Budget" />
                                    <Line type="monotone" dataKey="total_expense" stroke="#dc3545" name="Expense" />
                                </LineChart>
                            </ResponsiveContainer>
                        )}
                    </Modal.Body>
                    <Modal.Footer>

                    </Modal.Footer>
                </Modal>


            </div>
        </div>
    );
};

export default Overview;
