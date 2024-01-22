const product = [
    {
        id: 0,
        image: 'image/1.jpg',
        title: 't1',
        price: 120,
    },
    {
        id: 1,
        image: 'image/2.jpg',
        title: 't2',
        price: 60,
    },
    {
        id: 2,
        image: 'image/3.jpg',
        title: 't3',
        price: 230,
    },
    {
        id: 3,
        image: 'image/4.jpg',
        title: 't4',
        price: 230,
    },
    {
        id: 4,
        image: 'image/5.jpg',
        title: 't5',
        price: 230,
    },
    {
        id: 5,
        image: 'image/6.jpg',
        title: 't6',
        price: 230,
    },
];

const categories = [...new Set(product.map((item) => { return item }))]

document.getElementById('searchBar').addEventListener('keyup', (e) => {
    const searchData = e.target.value.toLowerCase();
    const filteredData = categories.filter((item) => {
        return (
            item.title.toLowerCase().includes(searchData)
        )
    })
    displayItem(filteredData)
});

const displayItem = (items) => {
    document.getElementById('root').innerHTML = items.map((item) => {
        var { image, title, price } = item;
        return (
            `<div class='box'>
                <div class='img-box'>
                    <img class='images' src=${image}></img>
                </div> 
                <div class='bottom'>
                    <p>${title}</p>
                    <h2>$ ${price}.00</h2>
                <button>Add to cart</button>
                </div>
            </div>`
        )
    }).join('')
};
displayItem(categories);

