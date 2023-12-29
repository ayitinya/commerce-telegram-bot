import { buildCollection, buildProperty } from "firecms";

enum ProductStatus {
    IN_STOCK = "IN_STOCK",
    OUT_OF_STOCK = "OUT_OF_STOCK",
    RUNNING_LOW = "RUNNING_LOW",
}

export type Product = {
    name: string;
    price: number;
    status: ProductStatus;
    image: string;
    description: string;
    published: boolean;
}


export const productsCollection = buildCollection<Product>({
    name: "Products",
    singularName: "Product",
    path: "products",
    icon: "LocalGroceryStore",
    group: "E-commerce",
    permissions: ({ authController, user }) => ({
        read: true,
        edit: true,
        create: true,
        delete: true
    }),
    properties: {
        name: {
            name: "Name",
            validation: { required: true },
            dataType: "string"
        },
        price: {
            name: "Price",
            validation: {
                required: true,
                requiredMessage: "You must set a price between 0 and 1000",
                min: 0,
                max: 1000
            },
            description: "Price with range validation",
            dataType: "number"
        },
        status: {
            name: "Status",
            validation: { required: true },
            dataType: "string",
            description: "Should this product be visible in the website",
            longDescription: "Example of a long description hidden under a tooltip. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Proin quis bibendum turpis. Sed scelerisque ligula nec nisi pellentesque, eget viverra lorem facilisis. Praesent a lectus ac ipsum tincidunt posuere vitae non risus. In eu feugiat massa. Sed eu est non velit facilisis facilisis vitae eget ante. Nunc ut malesuada erat. Nullam sagittis bibendum porta. Maecenas vitae interdum sapien, ut aliquet risus. Donec aliquet, turpis finibus aliquet bibendum, tellus dui porttitor quam, quis pellentesque tellus libero non urna. Vestibulum maximus pharetra congue. Suspendisse aliquam congue quam, sed bibendum turpis. Aliquam eu enim ligula. Nam vel magna ut urna cursus sagittis. Suspendisse a nisi ac justo ornare tempor vel eu eros.",
            enumValues: ProductStatus
        },
        published: {
            name: "Published",
            dataType: "boolean",
            columnWidth: 100,
        },
        image: buildProperty({ // The `buildProperty` method is a utility function used for type checking
            name: "Image",
            dataType: "string",
            storage: {
                storagePath: "images",
                acceptedFiles: ["image/*"]
            }
        }),
        description: {
            name: "Description",
            description: "This is the description of the product",
            multiline: true,
            longDescription: "Example of a long description hidden under a tooltip. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Proin quis bibendum turpis. Sed scelerisque ligula nec nisi pellentesque, eget viverra lorem facilisis. Praesent a lectus ac ipsum tincidunt posuere vitae non risus. In eu feugiat massa. Sed eu est non velit facilisis facilisis vitae eget ante. Nunc ut malesuada erat. Nullam sagittis bibendum porta. Maecenas vitae interdum sapien, ut aliquet risus. Donec aliquet, turpis finibus aliquet bibendum, tellus dui porttitor quam, quis pellentesque tellus libero non urna. Vestibulum maximus pharetra congue. Suspendisse aliquam congue quam, sed bibendum turpis. Aliquam eu enim ligula. Nam vel magna ut urna cursus sagittis. Suspendisse a nisi ac justo ornare tempor vel eu eros.",
            dataType: "string",
            columnWidth: 300
        },
    }
});
