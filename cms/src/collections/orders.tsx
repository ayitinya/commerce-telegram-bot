import { buildCollection, buildProperty } from "firecms";
import { Product } from "./products";

enum OrderState {
    PENDING = "PENDING",
    PROCESSING = "PROCESSING",
    IN_PROGRESS = "IN_PROGRESS",
    COMPLETED = "COMPLETED",
    CANCELLED = "CANCELLED",
}

type User = {
    id_: string;
    display_name: string;
    phone: string;
    address: string;
}

export type Order = {
    id_: string;
    user: User;
    state: OrderState;
    total_cost: number;
    items: {
        id_: string;
        product: Product;
        quantity: number;
    }[];
}


export const ordersCollection = buildCollection<Order>({
    name: "Orders",
    singularName: "Order",
    path: "orders",
    icon: "Order",
    group: "E-commerce",
    permissions: ({ authController, user }) => ({
        read: true,
        edit: true,
        create: true,
        delete: true
    }),
    properties: {
        id_: buildProperty({
            title: "ID",
            dataType: "string",
            readOnly: true
        }),
        user: buildProperty<User>({
            name : "User",
            dataType: "map",
            readOnly: true,
            properties: {
                id_: {
                    name: "ID",
                    dataType: "string",
                },
                display_name: {
                    name: "Display Name",
                    dataType: "string",
                },
                phone: {
                    name: "Phone",
                    dataType: "string",
                },
                address: {
                    name: "Address",
                    dataType: "string",
                    multiline: true,
                }
            }
        }),
        items: buildProperty({
            title: "Items",
            dataType: "array",
            of: buildProperty({
                title: "Item",
                dataType: "map",
                properties: {
                    id_: buildProperty({
                        title: "ID",
                        dataType: "string",
                        readOnly: true
                    }),
                    product: buildProperty({
                        title: "Product",
                        dataType: "reference",
                        collectionPath: "products"
                    }),
                    quantity: buildProperty({
                        title: "Quantity",
                        dataType: "number"
                    })
                }
            })
        }),
        
        state: buildProperty({
            title: "State",
            dataType: "string",
            enumValues: OrderState
        }),
        total_cost: buildProperty({
            title: "Total Cost",
            dataType: "number"
        }),
        
    }
});
