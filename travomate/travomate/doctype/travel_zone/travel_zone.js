// frappe.ui.form.on("Travel Zone", {
//     refresh: function (frm) {
//         // Initial setup
//         fetch_districts(frm);
//         fetch_guides(frm);

//         // Debug: Log the current state and district
//         console.log("Form loaded. State:", frm.doc.state, "District:", frm.doc.district);
//     },
//     state: function (frm) {
//         // Fetch districts when the state changes
//         fetch_districts(frm);

//         // Debug: Log the selected state
//         console.log("State changed to:", frm.doc.state);
//     },
//     district: function (frm) {
//         // Fetch areas when the district changes
//         fetch_areas(frm);

//         // Debug: Log the selected district
//         console.log("District changed to:", frm.doc.district);
//     },
//     guide: function (frm) {
//         // Fetch guides when the guide field is focused
//         fetch_guides(frm);

//         // Debug: Log the guide field focus
//         console.log("Guide field focused.");
//     }
// });

// // Function to fetch districts based on the selected state
// function fetch_districts(frm) {
//     if (!frm.doc.state) {
//         // Clear the district field if no state is selected
//         frm.set_value("district", "");
//         frm.refresh_field("district");
//         console.log("No state selected. Clearing district field.");
//         return;
//     }

//     frappe.call({
//         method: "travomate.custom_app.get_districts",
//         args: {
//             state: frm.doc.state // Pass the selected state as a filter
//         },
//         callback: function (response) {
//             if (response.message && response.message.status === "success") {
//                 const districts = response.message.data;

//                 // Set the options for the district field
//                 frm.set_df_property("district", "options", districts.map(function (district) {
//                     return {
//                         label: district.district_name, // Use the correct field name
//                         value: district.name
//                     };
//                 }));

//                 // Refresh the district field
//                 frm.refresh_field("district");

//                 // Debug: Log the fetched districts
//                 console.log("Fetched districts:", districts);
//             } else {
//                 console.error("Failed to fetch districts:", response.message);
//                 frappe.msgprint("Failed to fetch districts. Please try again.");
//             }
//         }
//     });
// }

// // Function to fetch areas based on the selected district
// function fetch_areas(frm) {
//     if (!frm.doc.district) {
//         // Clear the area field if no district is selected
//         frm.set_value("area", "");
//         frm.refresh_field("area");
//         console.log("No district selected. Clearing area field.");
//         return;
//     }

//     frappe.call({
//         method: "travomate.custom_app.get_areas",
//         args: {
//             district: frm.doc.district // Pass the selected district as a filter
//         },
//         callback: function (response) {
//             if (response.message && response.message.status === "success") {
//                 const areas = response.message.data;

//                 // Set the options for the area field
//                 frm.set_df_property("area", "options", areas.map(function (area) {
//                     return {
//                         label: area.area, // Use the correct field name
//                         value: area.name
//                     };
//                 }));

//                 // Refresh the area field
//                 frm.refresh_field("area");

//                 // Debug: Log the fetched areas
//                 console.log("Fetched areas:", areas);
//             } else {
//                 console.error("Failed to fetch areas:", response.message);
//                 frappe.msgprint("Failed to fetch areas. Please try again.");
//             }
//         }
//     });
// }

// // Function to fetch guides
// function fetch_guides(frm) {
//     frappe.call({
//         method: "travomate.custom_app.get_guides",
//         callback: function (response) {
//             if (response.message && response.message.status === "success") {
//                 const guides = response.message.data;

//                 // Set the options for the guide field
//                 frm.set_df_property("guide", "options", guides.map(function (guide) {
//                     return {
//                         label: guide.full_name, // Use the correct field name
//                         value: guide.name
//                     };
//                 }));

//                 // Refresh the guide field
//                 frm.refresh_field("guide");

//                 // Debug: Log the fetched guides
//                 console.log("Fetched guides:", guides);
//             } else {
//                 console.error("Failed to fetch guides:", response.message);
//                 frappe.msgprint("Failed to fetch guides. Please try again.");
//             }
//         }
//     });
// }

frappe.ui.form.on('Travel Zone', {
    district: function(frm) {
        // Clear the area field when district changes
        frm.set_value('area', '');

        // Set filter for the area field
        frm.set_query('area', function() {
            return {
                filters: {
                    district: frm.doc.district
                }
            };
        });
    }
});