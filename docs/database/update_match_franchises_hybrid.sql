-- Update the hybrid match function to support location filtering
create or replace function match_franchises_hybrid (
  query_embedding vector(1536),
  match_threshold float,
  match_count int default 10,
  max_budget int default null,
  location_filter text default null -- 'TX', 'NY', etc. (2 letter code)
)
returns table (
  id bigint,
  franchise_name text,
  primary_category text,
  sub_categories jsonb,
  description_text text,
  total_investment_min_usd int,
  similarity float,
  unavailable_states jsonb
)
language plpgsql
as $$
begin
  return query (
    select
      f.id,
      f.franchise_name,
      f.primary_category,
      f.sub_categories,
      f.description_text,
      f.total_investment_min_usd,
      1 - (f.franchise_embedding <=> query_embedding) as similarity,
      f.unavailable_states
    from
      "Franchises" f
    where
      -- 1. Similarity Threshold
      1 - (f.franchise_embedding <=> query_embedding) > match_threshold
      
      -- 2. Budget Filter (Hard Constraint)
      and (max_budget is null or f.total_investment_min_usd <= max_budget)
      
      -- 3. Location Filter (Knockout Shield)
      and (
        location_filter is null 
        or (
          -- Rule A: Exclude if explicit "Not Available" check exists for this state
          not exists (
            select 1 from territory_checks tc 
            where tc.franchise_id = f.id 
            and tc.state_code = location_filter 
            and tc.availability_status = 'Not Available'
          )
          -- Rule B: Exclude if state is in the static unavailable_states JSON list
          -- Note: unavailable_states is a JSON string array like '["NY", "CA"]'
          -- We cast to jsonb and check for containment.
          and (
             f.unavailable_states is null 
             or not (f.unavailable_states::jsonb ? location_filter)
          )
        )
      )
    order by
      f.franchise_embedding <=> query_embedding
    limit
      match_count
  );
end;
$$;
