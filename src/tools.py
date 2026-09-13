"""
🛠️ TOOL DEFINITIONS & EXECUTION BACKEND
Mã nguồn chứa danh sách Tool Schemas (JSON Schema) và Execution Layer phục vụ cho MCP Server.
"""

import json
from typing import Dict, Any

# ==============================================================================
# 1. KHAI BÁO TOOL SCHEMAS CHUẨN NATIVE JSON SCHEMA (TASK 1.2)
# ==============================================================================

TOOLS_SCHEMA = [
    # ==========================================================================
    # Tool 1: Tool mẫu - academic_query
    # ==========================================================================
    {
        "name": "academic_query",
        "description": "Tra cứu hồ sơ và thông tin học vụ của sinh viên VinUni bằng mã sinh viên.",
        "parameters": {
            "type": "object",
            "properties": {
                "student_id": {
                    "type": "string",
                    "description": "Mã sinh viên cần tra cứu (ví dụ: 'SV2026001')"
                }
            },
            "required": ["student_id"]
        }
    },

    # ==========================================================================
    # Tool 2: Tool mẫu - schedule_appointment
    # ==========================================================================
    {
        "name": "schedule_appointment",
        "description": "Đặt lịch hẹn tư vấn học vụ với Cố vấn học tập VinUni.",
        "parameters": {
            "type": "object",
            "properties": {
                "student_id": {
                    "type": "string",
                    "description": "Mã sinh viên cần đặt lịch (ví dụ: 'SV2026001')"
                },
                "datetime_str": {
                    "type": "string",
                    "description": "Thời gian hẹn (ví dụ: '14:00 15/09/2026')"
                },
                "advisor_name": {
                    "type": "string",
                    "description": "Tên cố vấn học tập"
                }
            },
            "required": [
                "student_id",
                "datetime_str",
                "advisor_name"
            ]
        }
    },

    # ==========================================================================
    # Tool 3: Facilities Agent - Kiểm tra phòng trống
    # ==========================================================================
    {
        "name": "check_room_availability",
        "description": "Kiểm tra các phòng họp còn trống theo thời gian và số lượng người.",
        "parameters": {
            "type": "object",
            "properties": {
                "datetime_str": {
                    "type": "string",
                    "description": "Thời gian cần đặt phòng, ví dụ '14:00 15/09/2026'"
                },
                "capacity": {
                    "type": "integer",
                    "description": "Số lượng người tham gia cuộc họp"
                }
            },
            "required": [
                "datetime_str",
                "capacity"
            ]
        }
    },

    # ==========================================================================
    # Tool 4: Facilities Agent - Kiểm tra thiết bị
    # ==========================================================================
    {
        "name": "check_room_equipment",
        "description": "Kiểm tra phòng họp có đáp ứng đầy đủ các thiết bị được yêu cầu hay không.",
        "parameters": {
            "type": "object",
            "properties": {
                "room_id": {
                    "type": "string",
                    "description": "Mã phòng họp cần kiểm tra, ví dụ 'A101'"
                },
                "required_equipment": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    },
                    "description": "Danh sách thiết bị yêu cầu, ví dụ ['máy chiếu', 'bảng trắng']"
                }
            },
            "required": [
                "room_id",
                "required_equipment"
            ]
        }
    },

    # ==========================================================================
    # Tool 5: Facilities Agent - Đặt phòng họp
    # ==========================================================================
    {
        "name": "book_meeting_room",
        "description": "Tạo booking cho phòng họp đã được xác nhận phù hợp với yêu cầu.",
        "parameters": {
            "type": "object",
            "properties": {
                "room_id": {
                    "type": "string",
                    "description": "Mã phòng họp cần đặt, ví dụ 'A101'"
                },
                "datetime_str": {
                    "type": "string",
                    "description": "Thời gian đặt phòng, ví dụ '14:00 15/09/2026'"
                },
                "capacity": {
                    "type": "integer",
                    "description": "Số lượng người tham gia cuộc họp"
                }
            },
            "required": [
                "room_id",
                "datetime_str",
                "capacity"
            ]
        }
    }
]

# ==============================================================================
# 2. MÔ PHỎNG DỮ LIỆU & HÀM THỰC THI TOOL (EXECUTION LAYER)
# ==============================================================================

MOCK_DATABASE = {
    # ==========================================================================
    # Dữ liệu sinh viên - GIỮ NGUYÊN
    # ==========================================================================
    "SV2026001": {
        "full_name": "Nguyễn Văn An",
        "class": "AI-K4",
        "gpa": 3.85,
        "email": "an.nv@vinuni.edu.vn",
        "status": "Đang học",
        "advisor": "PGS.TS Nguyễn Văn A"
    },

    "SV2026002": {
        "full_name": "Trần Thị Bình",
        "class": "AI-K4",
        "gpa": 3.60,
        "email": "binh.tt@vinuni.edu.vn",
        "status": "Đang học",
        "advisor": "TS. Lê Thị B"
    },

    # ==========================================================================
    # ADD: Dữ liệu phòng họp
    # ==========================================================================
    "rooms": {
        "A101": {
            "room_name": "A101",
            "capacity": 6,
            "equipment": [
                "máy chiếu",
                "bảng trắng"
            ]
        },

        "A102": {
            "room_name": "A102",
            "capacity": 8,
            "equipment": [
                "máy chiếu",
                "bảng trắng",
                "TV"
            ]
        },

        "B201": {
            "room_name": "B201",
            "capacity": 12,
            "equipment": [
                "máy chiếu",
                "bảng trắng",
                "TV",
                "micro"
            ]
        },

        "B202": {
            "room_name": "B202",
            "capacity": 20,
            "equipment": [
                "máy chiếu",
                "bảng trắng",
                "TV",
                "micro"
            ]
        }
    },

    # ==========================================================================
    # ADD: Booking hiện tại
    # ==========================================================================
    "bookings": [
        {
            "room_id": "A102",
            "datetime_str": "14:00 15/09/2026",
            "booked_by": "Team Beta"
        },
        {
            "room_id": "A101",
            "datetime_str": "09:00 16/09/2026",
            "booked_by": "Team Alpha"
        },
        {
            "room_id": "B201",
            "datetime_str": "15:00 17/09/2026",
            "booked_by": "Team Gamma"
        }
    ]
}


def execute_academic_query(student_id: str) -> str:
    """Thực thi tra cứu học vụ theo mã sinh viên"""
    student = MOCK_DATABASE.get(student_id.strip().upper())
    if student:
        return json.dumps({
            "status": "SUCCESS",
            "student_id": student_id,
            "data": student
        }, ensure_ascii=False)
    else:
        return json.dumps({
            "status": "NOT_FOUND",
            "message": f"Không tìm thấy dữ liệu sinh viên có mã '{student_id}'"
        }, ensure_ascii=False)


def execute_schedule_appointment(
    student_id: str,
    datetime_str: str,
    advisor_name: str = "PGS.TS Nguyễn Văn A"
) -> str:
    """Thực thi đặt lịch hẹn tư vấn học vụ"""
    return json.dumps({
        "status": "SUCCESS",
        "booking_id": f"BK-{student_id}-99",
        "student_id": student_id,
        "datetime": datetime_str,
        "advisor": advisor_name,
        "message": f"Đặt lịch thành công cho sinh viên {student_id} với {advisor_name} vào lúc {datetime_str}."
    }, ensure_ascii=False)


# ==============================================================================
# 3. FACILITIES TOOLS - EXECUTION LAYER
# ==============================================================================

def execute_check_room_availability(
    datetime_str: str,
    capacity: int
) -> str:
    """
    Kiểm tra các phòng họp còn trống theo thời gian và sức chứa.
    """

    available_rooms = []

    rooms = MOCK_DATABASE.get("rooms", {})
    bookings = MOCK_DATABASE.get("bookings", [])

    # Duyệt qua toàn bộ phòng
    for room_id, room_info in rooms.items():

        # Phòng phải đủ sức chứa
        if room_info["capacity"] < capacity:
            continue

        # Kiểm tra phòng có bị booking đúng thời gian hay không
        is_booked = any(
            booking["room_id"] == room_id
            and booking["datetime_str"] == datetime_str
            for booking in bookings
        )

        if not is_booked:
            available_rooms.append({
                "room_id": room_id,
                "room_name": room_info["room_name"],
                "capacity": room_info["capacity"],
                "equipment": room_info["equipment"]
            })

    if available_rooms:
        return json.dumps({
            "status": "SUCCESS",
            "datetime": datetime_str,
            "requested_capacity": capacity,
            "available_rooms": available_rooms
        }, ensure_ascii=False)

    return json.dumps({
        "status": "NOT_FOUND",
        "datetime": datetime_str,
        "requested_capacity": capacity,
        "message": (
            f"Không tìm thấy phòng họp còn trống phù hợp cho "
            f"{capacity} người vào lúc {datetime_str}."
        )
    }, ensure_ascii=False)


def execute_check_room_equipment(
    room_id: str,
    required_equipment: list
) -> str:
    """
    Kiểm tra phòng họp có đủ các thiết bị được yêu cầu hay không.
    """

    room_id = room_id.strip().upper()
    rooms = MOCK_DATABASE.get("rooms", {})

    room = rooms.get(room_id)

    # Không tìm thấy phòng
    if not room:
        return json.dumps({
            "status": "NOT_FOUND",
            "room_id": room_id,
            "message": f"Không tìm thấy phòng họp '{room_id}'."
        }, ensure_ascii=False)

    room_equipment = set(
        item.strip().lower()
        for item in room.get("equipment", [])
    )

    required = [
        item.strip().lower()
        for item in required_equipment
    ]

    missing_equipment = [
        item for item in required
        if item not in room_equipment
    ]

    if not missing_equipment:
        return json.dumps({
            "status": "SUCCESS",
            "room_id": room_id,
            "room_name": room["room_name"],
            "required_equipment": required_equipment,
            "available_equipment": room["equipment"],
            "message": f"Phòng {room_id} có đầy đủ thiết bị được yêu cầu."
        }, ensure_ascii=False)

    return json.dumps({
        "status": "NOT_FOUND",
        "room_id": room_id,
        "room_name": room["room_name"],
        "required_equipment": required_equipment,
        "available_equipment": room["equipment"],
        "missing_equipment": missing_equipment,
        "message": (
            f"Phòng {room_id} không có đủ thiết bị. "
            f"Thiếu: {', '.join(missing_equipment)}."
        )
    }, ensure_ascii=False)


def execute_book_meeting_room(
    room_id: str,
    datetime_str: str,
    capacity: int
) -> str:
    """
    Thực hiện đặt phòng họp.
    """

    room_id = room_id.strip().upper()
    rooms = MOCK_DATABASE.get("rooms", {})
    bookings = MOCK_DATABASE.setdefault("bookings", [])

    # Kiểm tra phòng có tồn tại
    room = rooms.get(room_id)

    if not room:
        return json.dumps({
            "status": "NOT_FOUND",
            "room_id": room_id,
            "message": f"Không tìm thấy phòng họp '{room_id}'."
        }, ensure_ascii=False)

    # Kiểm tra sức chứa
    if room["capacity"] < capacity:
        return json.dumps({
            "status": "INVALID",
            "room_id": room_id,
            "capacity": room["capacity"],
            "requested_capacity": capacity,
            "message": (
                f"Phòng {room_id} chỉ có sức chứa {room['capacity']} người, "
                f"không phù hợp với yêu cầu {capacity} người."
            )
        }, ensure_ascii=False)

    # Kiểm tra phòng đã được đặt chưa
    is_booked = any(
        booking["room_id"] == room_id
        and booking["datetime_str"] == datetime_str
        for booking in bookings
    )

    if is_booked:
        return json.dumps({
            "status": "CONFLICT",
            "room_id": room_id,
            "datetime": datetime_str,
            "message": (
                f"Phòng {room_id} đã được đặt vào lúc {datetime_str}. "
                "Vui lòng chọn phòng hoặc thời gian khác."
            )
        }, ensure_ascii=False)

    # Tạo booking mới
    booking_id = f"ROOM-{room_id}-{len(bookings) + 1:03d}"

    new_booking = {
        "booking_id": booking_id,
        "room_id": room_id,
        "datetime_str": datetime_str,
        "capacity": capacity,
        "booked_by": "Facilities Agent"
    }

    bookings.append(new_booking)

    return json.dumps({
        "status": "SUCCESS",
        "booking_id": booking_id,
        "room_id": room_id,
        "room_name": room["room_name"],
        "datetime": datetime_str,
        "capacity": capacity,
        "message": (
            f"Đặt phòng {room_id} thành công vào lúc "
            f"{datetime_str} cho {capacity} người."
        )
    }, ensure_ascii=False)


# ==============================================================================
# 4. TOOL ROUTER
# ==============================================================================

TOOL_ROUTER = {
    # Tool học vụ - GIỮ NGUYÊN
    "academic_query": execute_academic_query,
    "schedule_appointment": execute_schedule_appointment,

    # Facilities tools - ADD THÊM
    "check_room_availability": execute_check_room_availability,
    "check_room_equipment": execute_check_room_equipment,
    "book_meeting_room": execute_book_meeting_room
}


def dispatch_tool_call(tool_name: str, arguments: Dict[str, Any]) -> str:
    """Hàm trung chuyển thực thi tool"""
    if tool_name in TOOL_ROUTER:
        try:
            return TOOL_ROUTER[tool_name](**arguments)
        except Exception as e:
            return json.dumps({"status": "EXECUTION_ERROR", "error": str(e)}, ensure_ascii=False)
    return json.dumps({"status": "UNKNOWN_TOOL", "error": f"Tool '{tool_name}' không tồn tại!"}, ensure_ascii=False)
