import { useState } from 'react';
import { 
  Chart as ChartJS, 
  ArcElement, 
  Tooltip, 
  Legend, 
  CategoryScale, 
  LinearScale, 
  PointElement, 
  LineElement, 
  Title 
} from 'chart.js';
import { Doughnut, Line } from 'react-chartjs-2';
import { Calculator, ArrowRight, TrendingUp } from 'lucide-react';

ChartJS.register(
  ArcElement, 
  Tooltip, 
  Legend, 
  CategoryScale, 
  LinearScale, 
  PointElement, 
  LineElement, 
  Title
);

export default function Finance() {
  const [inputs, setInputs] = useState({
    tuition: 3500000,
    living: 1500000,
    loan: 2000000,
    salary: 6000000,
  });

  const [results, setResults] = useState(null);

  const calculateROI = (e) => {
    e.preventDefault();
    const totalCost = Number(inputs.tuition) + Number(inputs.living);
    const loanInterest = Number(inputs.loan) * 0.2; // roughly 20% over life of loan
    const trueCost = totalCost + loanInterest;
    
    // Net post-tax salary approx
    const netSalary = Number(inputs.salary) * 0.75; 
    
    // Assuming 30% of net salary goes to paying off the degree code and loans
    const yearlyPayoff = netSalary * 0.3;
    const breakEvenYears = trueCost / yearlyPayoff;
    const roi = ((netSalary * 5) - trueCost) / trueCost * 100; // 5 year ROI

    // 8-Year Timeline Simulation
    const labels = ['Year 0', 'Year 1', 'Year 2', 'Year 3', 'Year 4', 'Year 5', 'Year 6', 'Year 7', 'Year 8'];
    const cumulativePayoff = labels.map((_, i) => {
      if (i === 0) return -trueCost;
      return -trueCost + (yearlyPayoff * i);
    });

    setResults({
      totalCost,
      trueCost,
      breakEvenYears: breakEvenYears.toFixed(1),
      roi: roi.toFixed(1),
      chartData: {
        labels: ['Tuition', 'Living Costs', 'Loan Interest'],
        datasets: [
          {
            data: [inputs.tuition, inputs.living, loanInterest],
            backgroundColor: ['#7C6FF7', '#38BDF8', '#FB7185'],
            hoverOffset: 4,
          },
        ],
      },
      timelineData: {
        labels,
        datasets: [
          {
            label: 'Net Position (₹)',
            data: cumulativePayoff,
            borderColor: '#7C6FF7',
            backgroundColor: 'rgba(124, 111, 247, 0.1)',
            fill: true,
            tension: 0.4,
            pointRadius: 4,
            pointBackgroundColor: '#7C6FF7',
          },
        ],
      },
    });
  };

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center gap-4 mb-8">
        <div className="p-3 bg-gradient-to-br from-green-400 to-emerald-600 rounded-xl">
          <Calculator className="w-6 h-6 text-white" />
        </div>
        <div>
          <h1 className="text-3xl font-bold">Financial ROI Analyzer</h1>
          <p className="text-gray-400">Calculate the exact breakdown and break-even timeline for your studies.</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div className="glass-panel p-6">
          <h2 className="text-xl font-bold mb-6">Input Matrix</h2>
          <form onSubmit={calculateROI} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">Total Tuition (₹)</label>
              <input type="number" className="glass-input" value={inputs.tuition} onChange={e => setInputs({...inputs, tuition: e.target.value})} />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">Total Living Costs (₹)</label>
              <input type="number" className="glass-input" value={inputs.living} onChange={e => setInputs({...inputs, living: e.target.value})} />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">Loan Amount (₹)</label>
              <input type="number" className="glass-input" value={inputs.loan} onChange={e => setInputs({...inputs, loan: e.target.value})} />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">Expected Starting Salary (₹)</label>
              <input type="number" className="glass-input" value={inputs.salary} onChange={e => setInputs({...inputs, salary: e.target.value})} />
            </div>
            <button type="submit" className="btn-primary w-full mt-4 flex justify-center items-center gap-2">
              Calculate <ArrowRight className="w-4 h-4" />
            </button>
          </form>
        </div>

        {results && (
          <div className="flex flex-col gap-6">
            <div className="grid grid-cols-2 gap-4">
              <div className="glass-panel p-6 bg-gradient-to-br from-white/5 to-white/10 text-center">
                <div className="text-sm text-gray-400 mb-2">Break Even Time</div>
                <div className="text-3xl font-bold text-white">{results.breakEvenYears}<span className="text-lg text-gray-400 ml-1">yrs</span></div>
              </div>
              <div className="glass-panel p-6 bg-gradient-to-br from-white/5 to-white/10 text-center">
                <div className="text-sm text-gray-400 mb-2">5-Year ROI</div>
                <div className="text-3xl font-bold text-green-400">+{results.roi}%</div>
              </div>
              <div className="col-span-2 glass-panel p-6 text-center">
                <div className="text-sm text-gray-400 mb-2">True Cost of Education (with Interest)</div>
                <div className="text-4xl font-bold text-white">₹{results.trueCost.toLocaleString('en-IN')}</div>
              </div>
            </div>

            <div className="card p-6 flex flex-col items-center border-lavender/20">
              <h3 className="text-lg font-bold mb-4 w-full text-left flex items-center gap-2">
                <TrendingUp className="w-5 h-5 text-lavender"/> Performance Timeline
              </h3>
              <div className="w-full h-64">
                <Line 
                  data={results.timelineData} 
                  options={{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { 
                      legend: { display: false },
                      tooltip: { backgroundColor: '#1e293b', titleColor: '#fff', bodyColor: '#cbd5e1' } 
                    },
                    scales: { 
                      y: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#94a3b8', font: { size: 10 } } },
                      x: { grid: { display: false }, ticks: { color: '#94a3b8', font: { size: 10 } } }
                    }
                  }} 
                />
              </div>
            </div>

            <div className="card p-6 flex flex-col items-center border-sky-400/20">
              <h3 className="text-lg font-bold mb-4 w-full text-left">Cost Breakdown</h3>
              <div className="w-56 h-56">
                <Doughnut 
                  data={results.chartData} 
                  options={{
                    plugins: { 
                      legend: { position: 'bottom', labels: { color: '#64748b', font: { size: 10 }, padding: 20 } } 
                    },
                    cutout: '75%',
                    elements: { arc: { borderWidth: 0 } }
                  }} 
                />
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
