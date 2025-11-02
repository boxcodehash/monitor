export default async function handler(req, res) {
const { query, type } = req.query;


// Mock de productos
const items = [
{ title: `${query} - Variante 1`, price: `$${(Math.random() * 50 + 5).toFixed(2)}`, availability: Math.random() > 0.5 ? 'En stock' : 'Sin stock' },
{ title: `${query} - Variante 2`, price: `$${(Math.random() * 50 + 5).toFixed(2)}`, availability: Math.random() > 0.5 ? 'En stock' : 'Sin stock' }
];


res.status(200).json({ ok: true, items });
}
