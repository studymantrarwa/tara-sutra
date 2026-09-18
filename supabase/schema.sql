create extension if not exists pgcrypto;

create table if not exists profiles(
 id uuid primary key references auth.users(id) on delete cascade,
 full_name text,
 role text not null default 'user' check(role in ('user','astrologer','admin')),
 status text not null default 'active' check(status in ('active','suspended','blocked')),
 created_at timestamptz default now()
);

create table if not exists astrologers(
 id uuid primary key references profiles(id) on delete cascade,
 bio text,
 experience_years int default 0,
 specialization text,
 languages text[],
 fee numeric default 0,
 chat_fee numeric default 0,
 discount numeric default 0,
 verified boolean default false,
 online boolean default false,
 rating numeric default 0,
 approved_at timestamptz
);

create table if not exists kundalis(
 id uuid primary key default gen_random_uuid(),
 user_id uuid not null references profiles(id) on delete cascade,
 name text not null,
 gender text,
 dob date not null,
 birth_time time not null,
 place_label text not null,
 latitude double precision not null,
 longitude double precision not null,
 timezone text not null,
 calculation_data jsonb,
 created_at timestamptz default now()
);

create table if not exists conversations(
 id uuid primary key default gen_random_uuid(),
 created_by uuid not null references profiles(id),
 astrologer_id uuid references astrologers(id),
 status text default 'requested',
 created_at timestamptz default now()
);

create table if not exists conversation_participants(
 conversation_id uuid references conversations(id) on delete cascade,
 user_id uuid references profiles(id) on delete cascade,
 primary key(conversation_id,user_id)
);

create table if not exists messages(
 id uuid primary key default gen_random_uuid(),
 conversation_id uuid references conversations(id) on delete cascade,
 sender_id uuid references profiles(id),
 body text not null,
 created_at timestamptz default now(),
 seen_at timestamptz
);

create table if not exists reviews(
 id uuid primary key default gen_random_uuid(),
 consultation_id uuid,
 user_id uuid references profiles(id),
 astrologer_id uuid references astrologers(id),
 rating int check(rating between 1 and 5),
 review text,
 created_at timestamptz default now()
);

create table if not exists notifications(
 id uuid primary key default gen_random_uuid(),
 user_id uuid references profiles(id) on delete cascade,
 title text not null,
 body text,
 read_at timestamptz,
 created_at timestamptz default now()
);

alter table profiles enable row level security;
alter table kundalis enable row level security;
alter table conversations enable row level security;
alter table conversation_participants enable row level security;
alter table messages enable row level security;
alter table reviews enable row level security;
alter table notifications enable row level security;

create policy "profile self" on profiles for select using(auth.uid()=id);
create policy "kundli owner" on kundalis for all using(auth.uid()=user_id) with check(auth.uid()=user_id);
create policy "participant conversations" on conversations for select using(auth.uid()=created_by or auth.uid()=astrologer_id);
create policy "participant messages" on messages for select using(exists(select 1 from conversation_participants cp where cp.conversation_id=messages.conversation_id and cp.user_id=auth.uid()));
create policy "participant send messages" on messages for insert with check(sender_id=auth.uid() and exists(select 1 from conversation_participants cp where cp.conversation_id=messages.conversation_id and cp.user_id=auth.uid()));
create policy "own notifications" on notifications for select using(user_id=auth.uid());
